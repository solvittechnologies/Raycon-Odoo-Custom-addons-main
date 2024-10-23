# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang


class account_bank_reconciliation_report(models.AbstractModel):
    _name = 'account.bank.reconciliation.report'
    _description = 'Bank reconciliation report'

    line_number = 0

    @api.model
    def get_lines(self, context_id, line_id=None):
        return self.with_context(
            date_to=context_id.date_to,
            journal_id=context_id.journal_id,
            company_ids=context_id.company_ids.ids,
            context_id=context_id,
        )._lines()

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.context['journal_id'].currency_id or self.env.context['journal_id'].company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        return res

    def add_title_line(self, title, amount):
        self.line_number += 1
        return {
            'id': self.line_number,
            'type': 'line',
            'name': title,
            'footnotes': self.env.context['context_id']._get_footnotes('line', self.line_number),
            'columns': [self.env.context['date_to'], '', self._format(amount)],
            'level': 0,
        }

    def add_subtitle_line(self, title, amount=None):
        self.line_number += 1
        return {
            'id': self.line_number,
            'type': 'line',
            'name': title,
            'footnotes': self.env.context['context_id']._get_footnotes('line', self.line_number),
            'columns': ['', '', amount and self._format(amount) or ''],
            'level': 1,
        }

    def add_total_line(self, amount):
        self.line_number += 1
        return {
            'id': self.line_number,
            'type': 'line',
            'name': '',
            'footnotes': self.env.context['context_id']._get_footnotes('line', self.line_number),
            'columns': ["", "", self._format(amount)],
            'level': 2,
        }

    def add_bank_statement_line(self, line, amount):
        self.line_number += 1
        name = line.name
        return {
            'id': self.line_number,
            'statement_id': line.statement_id.id,
            'type': 'bank_statement_id',
            'name': len(name) >= 85 and name[0:80] + '...' or name,
            'footnotes': self.env.context['context_id']._get_footnotes('bank_statement_id', self.line_number),
            'columns': [line.date, line.ref, self._format(amount)],
            'level': 1,
        }

    @api.model
    def _lines(self):
        self.env['account.move.line'].check_access_rights('read')

        lines = []

        if not self.env.context['journal_id']:
            return lines

        #Start amount
        use_foreign_currency = bool(self.env.context['journal_id'].currency_id)
        account_ids = (self.env.context['journal_id'].default_debit_account_id + self.env.context['journal_id'].default_credit_account_id).ids

        if account_ids:
            self._cr.execute('''
                SELECT COALESCE(SUM(line.''' + ('amount_currency' if use_foreign_currency else 'balance') + '''), 0) FROM account_move_line line
                WHERE line.account_id IN %s AND line.date <= %s AND line.company_id IN %s
            ''', [
                tuple(account_ids),
                self.env.context['date_to'],
                tuple(self.env.context['company_ids']),
            ])
            start_amount = self._cr.fetchone()[0]
        else:
            start_amount = 0
        lines.append(self.add_title_line(_("Current Balance in GL"), start_amount))

        # Un-reconcilied bank statement lines
        aml_query = '''
            SELECT
                line.id                 AS id,
                line.name               AS name,
                line.date               AS date,
                line.ref                AS ref,
                line.amount_currency    AS amount_currency,
                line.balance            AS balance,
                line.payment_id         AS payment_id,
                line.statement_id       AS statement_id,
                move.id                 AS move_id,
                invoice.id              AS invoice_id,
                invoice.type            AS invoice_type
            FROM account_move_line line
            LEFT JOIN account_account_type account_type ON account_type.id = line.user_type_id
            LEFT JOIN account_invoice invoice ON invoice.id = line.invoice_id
            LEFT JOIN account_move move ON move.id = line.move_id
            LEFT JOIN account_bank_statement_line statement_line ON statement_line.id = move.statement_line_id
            WHERE line.journal_id = %s
            AND account_type.type = %s
            AND line.full_reconcile_id  IS NULL
            AND line.date <= %s
            AND line.company_id IN %s
            AND (move.statement_line_id IS NULL OR statement_line.date > %s)
            ORDER BY line.date DESC, line.id DESC
        '''
        aml_params = [
            self.env.context['journal_id'].id,
            'liquidity',
            self.env.context['date_to'],
            tuple(self.env.context['company_ids']),
            self.env.context['date_to'],
        ]
        # /!\ To forward-port until 12.0 (not included).
        account_bank_reconciliation_start = self._context.get('account_bank_reconciliation_start')
        if account_bank_reconciliation_start:
            aml_query = aml_query.replace('ORDER BY', 'AND line.date > %s ORDER BY')
            aml_params.append(account_bank_reconciliation_start)

        self._cr.execute(aml_query, aml_params)

        move_lines = self._cr.dictfetchall()
        unrec_tot = 0

        if move_lines:
            tmp_lines = []
            invoice_supplier_form_id = self.env.ref('account.invoice_supplier_form').id
            invoice_form_id = self.env.ref('account.invoice_form').id
            for line in move_lines:
                self.line_number += 1

                if line['statement_id']:
                     action = ['account.bank.statement', line['statement_id'], _('View Bank Statement'), False]
                elif line['payment_id']:
                    action = ['account.payment', line['payment_id'], _('View Payment'), False]
                elif line['invoice_id'] and line['invoice_type'] in ('in_invoice', 'in_refund'):
                    action = ['account.invoice', line['invoice_id'], _('View Invoice'), invoice_supplier_form_id]
                elif line['invoice_id'] and line['invoice_type'] not in ('in_invoice', 'in_refund'):
                    action = ['account.invoice', line['invoice_id'], _('View Invoice'), invoice_form_id]
                else:
                    action = ['account.move', line['move_id'], _('View Move'), False]

                tmp_lines.append({
                    'id': self.line_number,
                    'move_id': line['move_id'],
                    'type': 'move_line_id',
                    'action': action,
                    'name': line['name'],
                    'footnotes': self.env.context['context_id']._get_footnotes('move_line_id', self.line_number),
                    'columns': [line['date'], line['ref'], self._format(-(line['amount_currency'] if use_foreign_currency else line['balance']))],
                    'level': 1,
                })
                unrec_tot -= line['amount_currency'] if use_foreign_currency else line['balance']
            if unrec_tot > 0:
                title = _("Plus Unreconciled Payments")
            else:
                title = _("Minus Unreconciled Payments")
            lines.append(self.add_subtitle_line(title))
            lines += tmp_lines
            lines.append(self.add_total_line(unrec_tot))

        # Outstanding plus
        not_reconcile_plus = self.env['account.bank.statement.line'].search([('statement_id.journal_id', '=', self.env.context['journal_id'].id),
                                                                             ('date', '<=', self.env.context['date_to']),
                                                                             ('journal_entry_ids', '=', False),
                                                                             ('amount', '>', 0),
                                                                             ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_plus_tot = 0
        if not_reconcile_plus:
            lines.append(self.add_subtitle_line(_("Plus Unreconciled Statement Lines")))
            for line in not_reconcile_plus:
                lines.append(self.add_bank_statement_line(line, line.amount))
                outstanding_plus_tot += line.amount
            lines.append(self.add_total_line(outstanding_plus_tot))

        # Outstanding less
        not_reconcile_less = self.env['account.bank.statement.line'].search([('statement_id.journal_id', '=', self.env.context['journal_id'].id),
                                                                             ('date', '<=', self.env.context['date_to']),
                                                                             ('journal_entry_ids', '=', False),
                                                                             ('amount', '<', 0),
                                                                             ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_less_tot = 0
        if not_reconcile_less:
            lines.append(self.add_subtitle_line(_("Minus Unreconciled Statement Lines")))
            for line in not_reconcile_less:
                lines.append(self.add_bank_statement_line(line, line.amount))
                outstanding_less_tot += line.amount
            lines.append(self.add_total_line(outstanding_less_tot))

        # Final
        computed_stmt_balance = start_amount + outstanding_plus_tot + outstanding_less_tot + unrec_tot
        last_statement = self.env['account.bank.statement'].search([('journal_id', '=', self.env.context['journal_id'].id),
                                       ('date', '<=', self.env.context['date_to']), ('company_id', 'in', self.env.context['company_ids'])], order="date desc, id desc", limit=1)
        real_last_stmt_balance = last_statement.balance_end
        if computed_stmt_balance != real_last_stmt_balance:
            if real_last_stmt_balance - computed_stmt_balance > 0:
                title = _("Plus Missing Statements")
            else:
                title = _("Minus Missing Statements")
            lines.append(self.add_subtitle_line(title, real_last_stmt_balance - computed_stmt_balance))
        lines.append(self.add_title_line(_("Equal Last Statement Balance"), real_last_stmt_balance))
        return lines

    @api.model
    def get_title(self):
        return _("Bank Reconciliation")

    @api.model
    def get_name(self):
        return 'bank_reconciliation'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_nothing')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


class account_report_context_bank_reconciliation(models.TransientModel):
    _name = 'account.report.context.bank.rec'
    _description = 'A particular context for the bank reconciliation report'
    _inherit = 'account.report.context.common'

    def _get_bank_journals(self):
        self.journals = self.env['account.journal'].search([['type', '=', 'bank']])

    journal_id = fields.Many2one('account.journal', string=_("Bank account"))
    journals = fields.One2many('account.journal', string=_("Bank Accounts"), compute=_get_bank_journals)

    def get_report_obj(self):
        return self.env['account.bank.reconciliation.report']

    def get_columns_names(self):
        columns = [_("Date"), _("Reference"), _("Amount")]
        return columns

    @api.multi
    def get_columns_types(self):
        return ['date', 'text', 'number']

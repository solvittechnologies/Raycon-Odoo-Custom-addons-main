# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

import dateutil.parser
import StringIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    def _get_hide_journal_field(self):
        return self.env.context and 'journal_id' in self.env.context or False

    journal_id = fields.Many2one('account.journal', string='Journal',
        help="Accounting journal related to the bank statement you're importing. It has to be manually chosen "
             "for statement formats which doesn't allow automatic journal detection (QIF for example).")
    hide_journal_field = fields.Boolean(string='Hide the journal field in the view', default=_get_hide_journal_field)

    show_qif_date_format = fields.Boolean(default=False, store=False,
        help="Technical field used to ask the user for the date format used in the QIF file, as this format is ambiguous.")
    qif_date_format = fields.Selection([('month_first', "mm/dd/yy"), ('day_first', "dd/mm/yy")], string='Dates format', required=True, store=False,
        help="Although the historic QIF date format is month-first (mm/dd/yy), many financial institutions use the local format."
             "Therefore, it is frequent outside the US to have QIF date formated day-first (dd/mm/yy).")

    @api.onchange('data_file')
    def _onchange_data_file(self):
        file_content = self.data_file and base64.b64decode(self.data_file) or ""
        self.show_qif_date_format = self._check_qif(file_content)

    def _find_additional_data(self, *args):
        """ As .QIF format does not allow us to detect the journal, we need to let the user choose it.
            We set it in context in the same way it's done when calling the import action from a journal.
        """
        if self.journal_id:
            self.env.context = dict(self.env.context, journal_id=self.journal_id.id)
        return super(AccountBankStatementImport, self)._find_additional_data(*args)

    def _check_qif(self, data_file):
        return data_file.strip().startswith('!Type:')

    def _parse_file(self, data_file):
        if not self._check_qif(data_file):
            return super(AccountBankStatementImport, self)._parse_file(data_file)

        try:
            file_data = ""
            for line in StringIO.StringIO(data_file).readlines():
                file_data += line
            if '\r' in file_data:
                data_list = file_data.split('\r')
            else:
                data_list = file_data.split('\n')
            header = data_list[0].strip()
            header = header.split(":")[1]
        except:
            raise UserError(_('Could not decipher the QIF file.'))
        transactions = []
        vals_line = {}
        total = 0
        # Identified header types of the QIF format that we support.
        # Other types might need to be added. Here are the possible values
        # according to the QIF spec: Cash, Bank, CCard, Invst, Oth A, Oth L, Invoice.
        if header in ['Bank', 'Cash', 'CCard']:
            vals_bank_statement = {}
            for line in data_list:
                line = line.strip()
                if not line:
                    continue
                vals_line['sequence'] = len(transactions) + 1
                if line[0] == 'D':  # date of transaction
                    dayfirst = self.env.context.get('qif_date_format') == 'day_first'
                    vals_line['date'] = dateutil.parser.parse(line[1:], fuzzy=True, dayfirst=dayfirst).date()
                elif line[0] == 'T':  # Total amount
                    total += float(line[1:].replace(',', ''))
                    vals_line['amount'] = float(line[1:].replace(',', ''))
                elif line[0] == 'N':  # Check number
                    vals_line['ref'] = line[1:]
                elif line[0] == 'P':  # Payee
                    vals_line['name'] = 'name' in vals_line and line[1:] + ': ' + vals_line['name'] or line[1:]
                    # Since QIF doesn't provide account numbers, we'll have to find res.partner and res.partner.bank here
                    # (normal behavious is to provide 'account_number', which the generic module uses to find partner/bank)
                    partner_bank = self.env['res.partner.bank'].search([('partner_id.name', '=', line[1:])], limit=1)
                    if partner_bank:
                        vals_line['bank_account_id'] = partner_bank.id
                        vals_line['partner_id'] = partner_bank.partner_id.id
                elif line[0] == 'M':  # Memo
                    vals_line['name'] = 'name' in vals_line and vals_line['name'] + ': ' + line[1:] or line[1:]
                elif line[0] == '^':  # end of item
                    transactions.append(vals_line)
                    vals_line = {}
                elif line[0] == '\n':
                    transactions = []
                else:
                    pass
        else:
            raise UserError(_('This file is either not a bank statement or is not correctly formed.'))

        vals_bank_statement.update({
            'balance_end_real': total,
            'transactions': transactions
        })
        return None, None, [vals_bank_statement]

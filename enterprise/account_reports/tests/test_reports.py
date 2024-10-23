# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo.tests import common


class TestAccountReports(common.TransactionCase):
    def setUp(self):
        super(TestAccountReports, self).setUp()
        self.company = self.env.user.company_id

        self.partner_timmy_thomas = self.env['res.partner'].create({
            'name': 'Timmy Thomas',
        })

        #  Account types
        self.account_type_rcv = self.env['account.account.type'].create({
            'name': 'receivable',
            'type': 'receivable',
        })

        self.account_type_liq = self.env['account.account.type'].create({
            'name': 'liquidity',
            'type': 'liquidity',
        })

        self.account_type_other = self.env['account.account.type'].create({
            'name': 'other',
            'type': 'other',
        })

        # Accounts
        self.account_rcv = self.env['account.account'].create({
            'name': 'RCV',
            'code': '001',
            'user_type_id': self.account_type_rcv.id,
            'reconcile': True,
            'company_id': self.company.id,
        })

        self.account_sale = self.env['account.account'].create({
            'name': 'SALE',
            'code': '002',
            'user_type_id': self.account_type_other.id,
            'reconcile': False,
            'company_id': self.company.id,
        })

        self.account_expense = self.env['account.account'].create({
            'name': 'EXP',
            'code': '003',
            'user_type_id': self.account_type_other.id,
            'reconcile': False,
            'company_id': self.company.id,
        })

        self.account_pay = self.env['account.account'].create({
            'name': 'PAY',
            'code': '004',
            'user_type_id': self.account_type_liq.id,
            'reconcile': False,
            'company_id': self.company.id,
        })

        self.account_other = self.env['account.account'].create({
            'name': 'OTHER',
            'code': '005',
            'user_type_id': self.account_type_other.id,
            'reconcile': False,
            'company_id': self.company.id,
        })

        # Journals
        self.payment_journal = self.env['account.journal'].create({
            'name': 'payment',
            'code': 'PAY',
            'type': 'cash',
            'company_id': self.company.id,
            'default_debit_account_id': self.account_pay.id,
            'default_credit_account_id': self.account_pay.id,
        })

        self.sale_journal = self.env['account.journal'].create({
            'name': 'sale',
            'code': 'SALE',
            'type': 'sale',
            'company_id': self.company.id,
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })

    def test_00_financial_reports(self):
        for report in self.env['account.financial.html.report'].search([]):
            context_data = self.env['account.report.context.common'].return_context('account.financial.html.report', {}, report.id)
            self.env[context_data[0]].browse(context_data[1]).get_html_and_data()

    def test_01_custom_reports(self):
        report_models = [
            'account.bank.reconciliation.report',
            'account.general.ledger',
            'account.generic.tax.report',
        ]
        for report_model in report_models:
            context_data = self.env['account.report.context.common'].return_context(report_model, {})
            self.env[context_data[0]].browse(context_data[1]).get_html_and_data()

    def test_02_followup_reports(self):
        self.env['account.report.context.followup.all'].create({}).get_html({'page': 1})
        self.env['account.report.context.followup'].create({'partner_id': self.env.ref('base.res_partner_2').id}).get_html()

    def test_03_general_ledger(self):
        context = self.env['account.context.general.ledger'].create({})
        self.env['account.general.ledger'].get_lines(context.id)

    def test_04_general_ledger_output_cashbasis0(self):
        year = time.strftime('%Y')
        date_sale = year + '-06-26'
        date_payment = year + '-06-27'

        invoice_move = self.env['account.move'].create({
            'name': 'Invoice Move',
            'date': date_sale,
            'journal_id': self.sale_journal.id,
            'company_id': self.company.id,
        })

        # step sale
        sale_move_lines = self.env['account.move.line'].with_context(check_move_validity=False)
        sale_move_lines |= sale_move_lines.create({
            'name': 'receivable line',
            'account_id': self.account_rcv.id,
            'debit': 30.0,
            'move_id': invoice_move.id,
            'partner_id': self.partner_timmy_thomas.id,
        })
        sale_move_lines |= sale_move_lines.create({
            'name': 'product line',
            'account_id': self.account_sale.id,
            'credit': 30.0,
            'move_id': invoice_move.id,
            'partner_id': self.partner_timmy_thomas.id,
        })

        # step cost of product
        stock_move_lines = self.env['account.move.line'].with_context(check_move_validity=False)
        stock_move_lines |= stock_move_lines.create({
            'name': 'stock out line',
            'account_id': self.account_other.id,
            'credit': 5.0,
            'move_id': invoice_move.id,
            'partner_id': self.partner_timmy_thomas.id,
        })
        stock_move_lines |= stock_move_lines.create({
            'name': 'expense line',
            'account_id': self.account_expense.id,
            'debit': 5.0,
            'move_id': invoice_move.id,
            'partner_id': self.partner_timmy_thomas.id,
        })

        # step payment
        payment_move = self.env['account.move'].create({
            'name': 'payment move',
            'date': date_payment,
            'journal_id': self.payment_journal.id,
            'company_id': self.company.id,
        })

        payment_move_lines = self.env['account.move.line'].with_context(check_move_validity=False)
        payment_move_lines |= payment_move_lines.create({
            'name': 'receivable line',
            'credit': 30.0,
            'account_id': self.account_rcv.id,
            'partner_id': self.partner_timmy_thomas.id,
            'move_id': payment_move.id,
        })
        payment_move_lines |= payment_move_lines.create({
            'name': 'liquidity line',
            'debit': 30.0,
            'account_id': self.account_pay.id,
            'partner_id': self.partner_timmy_thomas.id,
            'move_id': payment_move.id,
        })

        invoice_move.post()
        payment_move.post()
        # reconcile
        aml_to_reconcile = (payment_move_lines | sale_move_lines).filtered(lambda l: not l.reconciled and l.account_id.internal_type == 'receivable')
        aml_to_reconcile.reconcile()
        partial_reconcile = self.env['account.partial.reconcile'].search([
            ('debit_move_id', 'in', aml_to_reconcile.ids),
            ('credit_move_id', 'in', aml_to_reconcile.ids)
        ])
        # Force reconcile at date
        self.env.cr.execute('UPDATE account_partial_reconcile SET create_date = %(date)s WHERE id in %(partial_ids)s',
            {'date': date_payment + ' 00:00:00',
             'partial_ids': tuple(partial_reconcile.ids)})

        # Build the report
        # With floats for numbers instead of currency formatted string
        GeneralLedger = self.env['account.general.ledger'].with_context(no_format=True)
        context_report = self.env['account.context.general.ledger'].create({
            'company_ids': [(6, False, self.company.ids)],
            'journal_ids': [(6, False, [self.payment_journal.id, self.sale_journal.id])],
            'date_filter': 'custom',
        })
        update_report = {
            'date_from': date_sale,
            'date_to': date_sale,
            'cash_basis': True,
        }

        # CASH BASIS TEST
        # Before Payment Date
        context_sale = context_report.return_context('account.general.ledger', update_report)[1]
        gl_lines_sale_cb = GeneralLedger.get_lines(context_sale)
        self.assertEqual(len(gl_lines_sale_cb), 0,
            'In cash basis, the general ledger before the payment date should be empty')

        # After Payment Date
        update_report['date_to'] = date_payment
        context_cashbasis = context_report.return_context('account.general.ledger', update_report)[1]
        gl_lines_pay_cb = GeneralLedger.get_lines(context_cashbasis)
        self.assertEqual(len(gl_lines_pay_cb), 5,
            'In cash basis, the general ledger should contain 5 lines after payment date')

        for line in gl_lines_pay_cb:
            name = line['name']
            columns = line['columns'][1:]  # just keep debit, credit and balance
            if name == '001 RCV':
                self.assertEqual(columns, [30.0, 30.0, 0.0])
            elif name == '002 SALE':
                self.assertEqual(columns, [0.0, 30.0, -30.0])
            elif name == '003 EXP':
                self.assertEqual(columns, [5.0, 0.0, 5.0])
            elif name == '004 PAY':
                self.assertEqual(columns, [30.0, 0.0, 30.0])
            elif name == '005 OTHER':
                self.assertEqual(columns, [0.0, 5.0, -5.0])

        # ACCRUAL TEST
        # Before Payment Date
        update_report['date_to'] = date_sale
        update_report['cash_basis'] = False
        context_accrual = context_report.return_context('account.general.ledger', update_report)[1]
        gl_lines_sale_acc = GeneralLedger.get_lines(context_accrual)

        self.assertEqual(len(gl_lines_sale_acc), 4,
            'In accrual, the general ledger should contain 4 lines before payment date')

        for line in gl_lines_sale_acc:
            name = line['name']
            columns = line['columns'][1:]
            if name == '001 RCV':
                self.assertEqual(columns, [30.0, 0.0, 30.0])
            elif name == '002 SALE':
                self.assertEqual(columns, [0.0, 30.0, -30.0])
            elif name == '003 EXP':
                self.assertEqual(columns, [5.0, 0.0, 5.0])
            elif name == '005 OTHER':
                self.assertEqual(columns, [0.0, 5.0, -5.0])

        # After payment Date
        update_report['date_to'] = date_payment
        update_report['cash_basis'] = False
        context_accrual = context_report.return_context('account.general.ledger', update_report)[1]
        gl_lines_pay_acc = GeneralLedger.get_lines(context_accrual)

        self.assertEqual(len(gl_lines_pay_acc), 5,
            'In accrual, the general ledger should contain 5 lines after payment date')

        for line in gl_lines_pay_acc:
            name = line['name']
            columns = line['columns'][1:]
            if name == '001 RCV':
                self.assertEqual(columns, [30.0, 30.0, 0.0])
            elif name == '002 SALE':
                self.assertEqual(columns, [0.0, 30.0, -30.0])
            elif name == '003 EXP':
                self.assertEqual(columns, [5.0, 0.0, 5.0])
            elif name == '004 PAY':
                self.assertEqual(columns, [30.0, 0.0, 30.0])
            elif name == '005 OTHER':
                self.assertEqual(columns, [0.0, 5.0, -5.0])

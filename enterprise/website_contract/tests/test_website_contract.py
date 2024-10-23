# -*- coding: utf-8 -*-
import calendar
import datetime
from dateutil.relativedelta import relativedelta

from .test_common import TestContractCommon
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger, float_utils
from odoo import fields


class TestContract(TestContractCommon):

    def test_templates(self):
        """ Test contract templates error when introducing duplicate option lines """

        with self.assertRaises(ValidationError):
            self.contract_tmpl_1.write({
                'subscription_template_option_ids': [(0, 0, {'product_id': self.product_opt.id, 'name': 'TestRecurringLine', 'uom_id': self.uom_base.id})]
            })

    @mute_logger('odoo.addons.base.ir.ir_model', 'odoo.models')
    def test_subscription(self):
        """ Test behaviour of subscription change """
        # switch plan: check that mandatory lines have been modified accordingly
        self.contract.change_subscription(self.contract_tmpl_2.id)
        self.assertEqual(self.contract.template_id.id, self.contract_tmpl_2.id, 'website_contract: template not changed when changing subscription from the frontend')
        self.assertEqual(len(self.contract.recurring_invoice_line_ids), 2, 'website_contract: number of lines after switching plan does not match mandatory lines of new plan')
        self.assertEqual(self.contract.recurring_total, 650, 'website_contract: price after switching plan is wrong')

        # add option
        self.contract.add_option(self.contract_tmpl_2.subscription_template_option_ids.id)
        self.assertEqual(len(self.contract.recurring_invoice_line_ids), 3, 'website_contract: number of lines after adding option does not add up')
        self.assertEqual(self.contract.recurring_total, 850, 'website_contract: recurring price after adding option is wrong')

        # switch back: option should be preserved, other lines should have been changed
        self.contract.change_subscription(self.contract_tmpl_1.id)
        self.assertEqual(len(self.contract.recurring_invoice_line_ids), 2, 'website_contract: number of lines after switching plan twice does add up')
        self.assertEqual(self.contract.recurring_total, 70, 'website_contract: recurring price after switching plan twice is wrong')

    def test_upsell(self):
        self.sale_order = self.env['sale.order'].create({
            'name': 'TestSO',
            'project_id': self.contract.analytic_account_id.id,
            'subscription_id': self.contract.id,
            'partner_id': self.user_portal.partner_id.id,
        })
        current_year = int(datetime.datetime.strftime(datetime.date.today(), '%Y'))
        current_day = datetime.datetime.now().timetuple().tm_yday
        self.contract.recurring_next_date = '%s-01-01' % (current_year + 1)
        is_leap = calendar.isleap(current_year)
        fraction = float(current_day) / (365.0 if not is_leap else 366.0)
        self.contract.partial_invoice_line(self.sale_order, self.contract_tmpl_1.subscription_template_option_ids)
        invoicing_ratio = self.sale_order.order_line.discount / 100.0
        # discount should be equal to prorata as computed here
        self.assertEqual(float_utils.float_compare(fraction, invoicing_ratio, precision_digits=2), 0, 'website_contract: partial invoicing ratio calculation mismatch')
        self.sale_order.action_confirm()
        self.assertEqual(len(self.contract.recurring_invoice_line_ids), 2, 'website_contract: number of lines after adding pro-rated discounted option does not add up')
        # there should be no discount on the contract line in this case
        self.assertEqual(self.contract.recurring_total, 70, 'website_contract: price after adding pro-rated discounted option does not add up')

    def test_auto_close(self):
        """Ensure a 15 days old 'online payment' subscription gets closed if no token is set."""
        self.contract_tmpl_3.payment_mandatory = True
        self.contract.write({
            'recurring_next_date': fields.Date.to_string(datetime.date.today() - relativedelta(days=15)),
            'template_id': self.contract_tmpl_3.id,
        })
        self.contract.with_context(auto_commit=False)._recurring_create_invoice(automatic=True)
        self.assertEqual(self.contract.state, 'close', 'website_contrect: subscription with online payment and no payment method set should get closed after 15 days')

    # Mocking for 'test_auto_payment_with_token'
    # Necessary to have a valid and done transaction when the cron on subscription passes through
    def _mock_subscription_do_payment(self, payment_method, invoice, two_steps_sec=True):
        tx_obj = self.env['payment.transaction']
        reference = "CONTRACT-%s-%s" % (self.id, datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
        values = {
            'amount': invoice.amount_total,
            'acquirer_id': self.acquirer.id,
            'type': 'server2server',
            'currency_id': invoice.currency_id.id,
            'reference': reference,
            'payment_token_id': payment_method.id,
            'partner_id': invoice.partner_id.id,
            'partner_country_id': invoice.partner_id.country_id.id,
            'invoice_id': invoice.id,
            'state': 'done',
        }
        tx = tx_obj.create(values)
        return tx

    # Mocking for 'test_auto_payment_with_token'
    # Otherwise the whole sending mail process will be triggered
    # And we are not here to test that flow, and it is a heavy one
    def _mock_subscription_send_success_mail(self, tx, invoice):
        self.mock_send_success_count += 1
        return 666

    # Mocking for 'test_auto_payment_with_token'
    # Avoid account_id is False when creating the invoice
    def _mock_prepare_invoice_data(self):
        invoice = self.original_prepare_invoice_data()
        invoice['account_id'] = self.account_receivable.id
        invoice['partner_bank_id'] = False
        return invoice

    # Mocking for 'test_auto_payment_with_token'
    # Avoid account_id is False when creating the invoice
    def _mock_prepare_invoice_line(self, line, fiscal_position):
        line_values = self.original_prepare_invoice_line(line, fiscal_position)
        line_values['account_id'] = self.account_receivable.id
        return line_values

    def test_auto_payment_with_token(self):
        from mock import patch

        self.company = self.env.user.company_id

        self.account_type_receivable = self.env['account.account.type'].create(
            {'name': 'receivable',
             'type': 'receivable'})

        self.account_receivable = self.env['account.account'].create(
            {'name': 'Ian Anderson',
             'code': 'IA',
             'user_type_id': self.account_type_receivable.id,
             'company_id': self.company.id,
             'reconcile': True})

        self.sale_journal = self.env['account.journal'].create(
            {'name': 'reflets.info',
            'code': 'ref',
            'type': 'sale',
            'company_id': self.company.id,
            'sequence_id': self.env['ir.sequence'].search([], limit=1).id,
            'default_credit_account_id': self.account_receivable.id,
            'default_debit_account_id': self.account_receivable.id})

        self.partner = self.env['res.partner'].create(
            {'name': 'Stevie Nicks',
             'email': 'sti@fleetwood.mac',
             'property_account_receivable_id': self.account_receivable.id,
             'property_account_payable_id': self.account_receivable.id,
             'company_id': self.company.id,
             'customer': True})

        self.acquirer = self.env['payment.acquirer'].create(
            {'name': 'The Wire',
            'provider': 'transfer',
            'company_id': self.company.id,
            'auto_confirm': 'none',
            'environment': 'test',
            'view_template_id': self.env['ir.ui.view'].search([('type', '=', 'qweb')], limit=1).id})

        self.payment_method = self.env['payment.token'].create(
            {'name': 'Jimmy McNulty',
             'partner_id': self.partner.id,
             'acquirer_id': self.acquirer.id,
             'acquirer_ref': 'Omar Little'})

        self.original_prepare_invoice_data = self.contract._prepare_invoice_data
        self.original_prepare_invoice_line = self.contract._prepare_invoice_line

        patchers = [
            patch('odoo.addons.website_contract.models.sale_subscription.SaleSubscription._prepare_invoice_line', wraps=self._mock_prepare_invoice_line, create=True),
            patch('odoo.addons.website_contract.models.sale_subscription.SaleSubscription._prepare_invoice_data', wraps=self._mock_prepare_invoice_data, create=True),
            patch('odoo.addons.website_contract.models.sale_subscription.SaleSubscription._do_payment', wraps=self._mock_subscription_do_payment, create=True),
            patch('odoo.addons.website_contract.models.sale_subscription.SaleSubscription.send_success_mail', wraps=self._mock_subscription_send_success_mail, create=True),
        ]

        for patcher in patchers:
            patcher.start()

        self.contract_tmpl_3.payment_mandatory = True

        self.contract.write({
            'partner_id': self.partner.id,
            'recurring_next_date': fields.Date.to_string(datetime.date.today()),
            'template_id': self.contract_tmpl_3.id,
            'company_id': self.company.id,
            'payment_token_id': self.payment_method.id
        })
        self.mock_send_success_count = 0
        self.contract.with_context(auto_commit=False)._recurring_create_invoice(automatic=True)
        self.assertEqual(self.mock_send_success_count, 1, 'website_contract: a mail to the invoice recipient should have been sent')
        self.assertEqual(self.contract.state, 'open', 'website_contract: subscription with online payment and a payment method set should stay opened when transaction succeeds')
        invoice = self.env['account.invoice'].search(self.contract.action_subscription_invoice()['domain'])[0]
        recurring_total_with_taxes = self.contract.recurring_total + (self.contract.recurring_total * (self.percent_tax.amount / 100.0))
        self.assertEqual(invoice.amount_total, recurring_total_with_taxes, 'website_contract: the total of the recurring invoice created should be the contract recurring total + the products taxes')
        self.assertTrue(all(line.invoice_line_tax_ids.ids == self.percent_tax.ids for line in invoice.invoice_line_ids), 'website_contract: All lines of the recurring invoice created should have the percent tax set on the contract products')
        self.assertTrue(all(tax_line.tax_id == self.percent_tax for tax_line in invoice.tax_line_ids), 'The invoice tax lines should be set and should all use the tax set on the contract products')

        for patcher in patchers:
            patcher.stop()

    def test_sub_creation(self):
        order = self.env['sale.order'].create({
            'name': 'TestSOTemplate',
            'partner_id': self.user_portal.partner_id.id,
            'template_id': self.quote_template.id,
        })

        order.onchange_template_id()
        order.action_confirm()
        self.assertTrue(order.subscription_id, 'website_contract: subscription is not created at so confirmation')
        self.assertEqual(order.subscription_management, 'create', 'website_contract: subscription creation should set the so to "create"')
        self.assertEqual(order.project_id.name,
                         '%s - %s' % (order.partner_id.name, order.subscription_id.code),
                         '''website_contract: analytic account created along subscription
                         should be named as <Subscription code> - <Partner name>''')

    def test_no_aa_renaming(self):
        initial_aa_name = 'InitialName'
        analytic = self.env['account.analytic.account'].create({
            'partner_id': self.user_portal.partner_id.id,
            'name': initial_aa_name
        })
        order = self.env['sale.order'].create({
            'name': 'TestSOTemplate',
            'partner_id': self.user_portal.partner_id.id,
            'template_id': self.quote_template.id,
            'project_id': analytic.id,
        })

        order.onchange_template_id()
        order.action_confirm()
        self.assertEqual(analytic.name,
                         initial_aa_name,
                         'website_contract: subscription creation should not rename an existing AA')

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource


class TestOfxFile(TransactionCase):
    """ Tests for import bank statement ofx file format (account.bank.statement.import) """

    def test_ofx_file_import(self):
        # Get OFX file content
        ofx_file_path = get_module_resource('account_bank_statement_import_ofx', 'test_ofx_file', 'test_ofx.ofx')
        ofx_file = open(ofx_file_path, 'rb').read().encode('base64')

        # Create a bank account and journal corresponding to the OFX file (same currency and account number)
        bank_journal_id = self.env['account.journal'].create({'name': 'Bank 123456', 'code': 'BNK67', 'type': 'bank',
            'currency_id': self.env.ref("base.USD").id,
            'bank_acc_number': '123456'}).id

        # Use an import wizard to process the file
        import_wizard = self.env['account.bank.statement.import'].with_context(journal_id=bank_journal_id).create({'data_file': ofx_file, 'filename': 'test_ofx.ofx'})
        import_wizard.import_file()

        # Check the imported bank statement
        bank_st_record = self.env['account.bank.statement'].search([('reference', '=', 'test_ofx.ofx')])[0]
        self.assertEqual(bank_st_record.balance_start, 2516.56)
        self.assertEqual(bank_st_record.balance_end_real, 2156.56)

        # Check an imported bank statement line
        line = bank_st_record.line_ids.filtered(lambda r: r.unique_import_id == '123456-'+str(bank_journal_id)+'-219378')
        self.assertEqual(line.name, 'Agrolait')
        self.assertEqual(line.amount, -80)
        self.assertEqual(line.partner_id.id, self.ref('base.res_partner_2'))
        self.assertEqual(line.bank_account_id.id, self.ref('account_bank_statement_import.ofx_partner_bank_1'))

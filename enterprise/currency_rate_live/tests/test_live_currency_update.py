import unittest
from odoo.tests.common import TransactionCase


class CurrencyTestCase(TransactionCase):

    @unittest.skip("Currency rate live test disabled as it requires to contact external servers")
    def test_live_currency_update(self):
        company_ecb = self.env['res.company'].create({'name': 'TEST ECB', 'currency_provider': 'ecb'})

        #check the number of rates for USD
        self.currency_usd = self.env.ref('base.USD')
        rates_number = len(self.currency_usd.rate_ids)

        #get the live rate for both companies, each one with a different method
        res_ecb = company_ecb._update_currency_ecb()

        #Check that both company call to company_ecb.update_currency_rates() has created a new rate for the USD (only if the request was a success)
        rates_number_again = len(self.currency_usd.rate_ids)
        self.assertEqual(rates_number + int(res_ecb), rates_number_again)

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
from odoo import models, fields, api


class EbayConfiguration(models.TransientModel):
    _name = 'sale.config.settings'
    _inherit = 'sale.config.settings'

    ebay_dev_id = fields.Char("Developer Key")
    ebay_sandbox_token = fields.Text("Sandbox Token")
    ebay_sandbox_app_id = fields.Char("Sandbox App Key")
    ebay_sandbox_cert_id = fields.Char("Sandbox Cert Key")

    ebay_prod_token = fields.Text("Production Token")
    ebay_prod_app_id = fields.Char("Production App Key")
    ebay_prod_cert_id = fields.Char("Production Cert Key")
    ebay_domain = fields.Selection([
        ('prod', 'Production'),
        ('sand', 'Sandbox'),
    ], string='eBay Site', default='sand', required=True)
    ebay_currency = fields.Many2one("res.currency", string='eBay Currency',
                                    domain=[('ebay_available', '=', True)], required=True)
    ebay_country = fields.Many2one("res.country", domain=[('ebay_available', '=', True)],
                                   string="Country Where The Products Are Stored")
    ebay_site = fields.Many2one("ebay.site", string="eBay Site Used")
    ebay_zip_code = fields.Char(string="Zip Code Where The Products Are Stored")
    ebay_location = fields.Char(string="Location Where The Products Are Stored")
    ebay_out_of_stock = fields.Boolean("Use Out Of Stock Option", default=False)
    ebay_sales_team = fields.Many2one("crm.team", string="Sales Team")
    ebay_gallery_plus = fields.Boolean("Use Gallery Plus Option", default=False)

    @api.multi
    def set_ebay(self):
        ebay_dev_id = self[0].ebay_dev_id or ''
        self.env['ir.config_parameter'].set_param('ebay_dev_id', ebay_dev_id, groups=["base.group_system"])
        ebay_sales_team = self[0].ebay_sales_team or self.env['crm.team'].search([])[0]
        self.env['ir.config_parameter'].set_param('ebay_sales_team', ebay_sales_team.id)
        sandbox_token = self[0].ebay_sandbox_token or ''
        self.env['ir.config_parameter'].set_param('ebay_sandbox_token', sandbox_token, groups=["base.group_system"])
        sandbox_app_id = self[0].ebay_sandbox_app_id or ''
        self.env['ir.config_parameter'].set_param('ebay_sandbox_app_id', sandbox_app_id, groups=["base.group_system"])
        sandbox_cert_id = self[0].ebay_sandbox_cert_id or ''
        self.env['ir.config_parameter'].set_param('ebay_sandbox_cert_id', sandbox_cert_id, groups=["base.group_system"])
        prod_token = self[0].ebay_prod_token or ''
        self.env['ir.config_parameter'].set_param('ebay_prod_token', prod_token, groups=["base.group_system"])
        prod_app_id = self[0].ebay_prod_app_id or ''
        self.env['ir.config_parameter'].set_param('ebay_prod_app_id', prod_app_id, groups=["base.group_system"])
        prod_cert_id = self[0].ebay_prod_cert_id or ''
        self.env['ir.config_parameter'].set_param('ebay_prod_cert_id', prod_cert_id, groups=["base.group_system"])
        domain = self[0].ebay_domain or ''
        self.env['ir.config_parameter'].set_param('ebay_domain', domain)
        currency = self[0].ebay_currency or self.env['res.currency'].search(
            [('ebay_available', '=', True)])[0]
        self.env['ir.config_parameter'].set_param('ebay_currency', currency.id)
        # by default all currencies active field is set to False except EUR and USD
        self[0].ebay_currency.active = True
        country = self[0].ebay_country or self.env['res.country'].search(
            [('ebay_available', '=', True)])[0]
        self.env['ir.config_parameter'].set_param('ebay_country', country.id)
        site = self[0].ebay_site or self.env['ebay.site'].search([])[0]
        self.env['ir.config_parameter'].set_param('ebay_site', site.id)
        zip_code = self[0].ebay_zip_code or ''
        self.env['ir.config_parameter'].set_param('ebay_zip_code', zip_code)
        location = self[0].ebay_location or ''
        self.env['ir.config_parameter'].set_param('ebay_location', location)
        gallery_plus = self[0].ebay_gallery_plus or ''
        self.env['ir.config_parameter'].set_param('ebay_gallery_plus', gallery_plus)
        out_of_stock = self[0].ebay_out_of_stock or ''
        if out_of_stock != self.env['ir.config_parameter'].get_param('ebay_out_of_stock'):
            self.env['ir.config_parameter'].set_param('ebay_out_of_stock', out_of_stock)

            if domain == 'sand':
                if sandbox_token and sandbox_cert_id and sandbox_app_id:
                    ebay_api = Trading(
                        domain='api.sandbox.ebay.com',
                        config_file=None,
                        appid=sandbox_app_id,
                        devid="ed74122e-6f71-4877-83d8-e0e2585bd78f",
                        certid=sandbox_cert_id,
                        token=sandbox_token,
                        siteid=site.ebay_id if site else 0)
                    call_data = {
                        'OutOfStockControlPreference': 'true' if out_of_stock else 'false',
                    }
                    try:
                        ebay_api.execute('SetUserPreferences', call_data)
                    except ConnectionError:
                        pass
            else:
                if prod_token and prod_cert_id and prod_app_id:
                    ebay_api = Trading(
                        domain='api.ebay.com',
                        config_file=None,
                        appid=prod_app_id,
                        devid="ed74122e-6f71-4877-83d8-e0e2585bd78f",
                        certid=prod_cert_id,
                        token=prod_token,
                        siteid=site.ebay_id if site else 0)
                    call_data = {
                        'OutOfStockControlPreference': 'true' if out_of_stock else 'false',
                    }
                    try:
                        ebay_api.execute('SetUserPreferences', call_data)
                    except ConnectionError:
                        pass

    @api.model
    def get_default_ebay(self, fields):
        params = self.env['ir.config_parameter'].sudo()
        ebay_dev_id = params.get_param('ebay_dev_id', default='')
        ebay_sandbox_token = params.get_param('ebay_sandbox_token', default='')
        ebay_sandbox_app_id = params.get_param('ebay_sandbox_app_id', default='')
        ebay_sandbox_cert_id = params.get_param('ebay_sandbox_cert_id', default='')
        ebay_prod_token = params.get_param('ebay_prod_token', default='')
        ebay_prod_app_id = params.get_param('ebay_prod_app_id', default='')
        ebay_prod_cert_id = params.get_param('ebay_prod_cert_id', default='')
        ebay_domain = params.get_param('ebay_domain', default='sand')
        ebay_currency = int(params.get_param('ebay_currency', default=self.env.ref('base.USD')))
        ebay_country = int(params.get_param('ebay_country', default=self.env.ref('base.us')))
        ebay_site = int(params.get_param('ebay_site',
                        default=self.env['ebay.site'].search([])[0]))
        ebay_zip_code = params.get_param('ebay_zip_code')
        ebay_location = params.get_param('ebay_location')
        ebay_out_of_stock = params.get_param('ebay_out_of_stock', default=False)
        ebay_sales_team = int(params.get_param('ebay_sales_team',
                              default=self.env['crm.team'].search([], limit=1)))
        ebay_gallery_plus = params.get_param('ebay_gallery_plus')
        return {'ebay_dev_id': ebay_dev_id,
                'ebay_sandbox_token': ebay_sandbox_token,
                'ebay_sandbox_app_id': ebay_sandbox_app_id,
                'ebay_sandbox_cert_id': ebay_sandbox_cert_id,
                'ebay_prod_token': ebay_prod_token,
                'ebay_prod_app_id': ebay_prod_app_id,
                'ebay_prod_cert_id': ebay_prod_cert_id,
                'ebay_domain': ebay_domain,
                'ebay_currency': ebay_currency,
                'ebay_country': ebay_country,
                'ebay_site': ebay_site,
                'ebay_zip_code': ebay_zip_code,
                'ebay_location': ebay_location,
                'ebay_out_of_stock': ebay_out_of_stock,
                'ebay_sales_team': ebay_sales_team,
                'ebay_gallery_plus': ebay_gallery_plus,
                }

    @api.model
    def button_sync_categories(self, context=None):
        self.env['ebay.category']._cron_sync()

    @api.model
    def button_sync_product_status(self, context=None):
        self.env['product.template'].sync_product_status()

    @api.model
    def sync_policies(self, context=None):
        self.env['ebay.policy'].sync_policies()

    @api.model
    def sync_ebay_details(self, context=None):
        response = self.env['product.template'].ebay_execute(
            'GeteBayDetails',
            {'DetailName': ['CountryDetails', 'SiteDetails', 'CurrencyDetails']}
        )
        for country in self.env['res.country'].search([('ebay_available', '=', True)]):
            country.ebay_available = False
        for country in response.dict()['CountryDetails']:
            record = self.env['res.country'].search([('code', '=', country['Country'])])
            if record:
                record.ebay_available = True
        for currency in self.env['res.currency'].search([('ebay_available', '=', True)]):
            currency.ebay_available = False
        for currency in response.dict()['CurrencyDetails']:
            record = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency['Currency'])])
            if record:
                record.ebay_available = True
        for site in response.dict()['SiteDetails']:
            record = self.env['ebay.site'].search([('ebay_id', '=', site['SiteID'])])
            if not record:
                record = self.env['ebay.site'].create({
                    'name': site['Site'],
                    'ebay_id': site['SiteID']
                })
            else:
                record.name = site['Site']

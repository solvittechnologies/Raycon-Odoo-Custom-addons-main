from odoo import fields, models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    type_tax_use = fields.Selection([('sale', 'Sales'),
                                     ('purchase', 'Purchases'),
                                     ('none', 'None'),
                                     ('adjustment', 'Adjustment'),
                                     ('expenses','Expenses'),
                                     ('assets','Assets')],
                                    string='Tax Scope', required=True, default="sale",
                                    help="Determines where the tax is selectable. Note : 'None' means a tax can't be used by itself, however it can still be used in a group. 'adjustment' is used to perform tax adjustment.")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        vals = super(AccountInvoiceLine, self)._onchange_product_id()
        self.name = ''
        return vals

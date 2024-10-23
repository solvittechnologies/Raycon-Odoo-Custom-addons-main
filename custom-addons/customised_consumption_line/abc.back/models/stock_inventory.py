# -*- coding: utf-8 -*-

from odoo import fields, models,api



class StockInventory(models.Model):
    _inherit = "stock.inventory"


    def action_validate(self):
        res = super(StockInventory, self).action_validate()
        for rec in self.line_ids:
            self.env['stock.quant'].create({
                'location_id':self.site_name.id,
                'product_id':rec.product_id.id,
                'quantity':rec.theoretical_qty
            })
        return res

class InventoryLineInherit(models.Model):
    _inherit = "stock.inventory.line"

    theoretical_qty = fields.Float('Theoretical Quantity', readonly=False,store=True,default=0.0,compute=False)

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        pass

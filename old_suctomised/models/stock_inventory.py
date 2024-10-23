# -*- coding: utf-8 -*-

from odoo import fields, models,api



class InventoryLineInherit(models.Model):
    _inherit = "stock.inventory.line"

    theoretical_qty = fields.Float('Theoretical Quantity', readonly=False,store=True,default=0.0,compute=False)

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        pass
        # if not self.product_id:
        #     self.theoretical_qty = 0
        #     return
        # theoretical_qty = self.product_id.get_theoretical_quantity(
        #     self.product_id.id,
        #     self.location_id.id,
        #     lot_id=self.prod_lot_id.id,
        #     package_id=self.package_id.id,
        #     owner_id=self.partner_id.id,
        #     to_uom=self.product_uom_id.id,
        # )
        # self.theoretical_qty = theoretical_qty
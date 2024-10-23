# -*- coding: utf-8 -*-

from odoo import fields, models,api



class StockInventory(models.Model):
    _inherit = "stock.inventory"


    def action_validate(self):
        res = super(StockInventory, self).action_validate()
        for rec in self.line_ids:
            if self.is_material_consumption == True:
                self.env['stock.quant'].create({
                    'location_id':self.site_name.id,
                    'product_id':rec.product_id.id,
                    'quantity':rec.theoretical_qty
                })
        return res

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(StockInventory, self).default_get(fields_list)
    #     # def_site = self.env['stock.location'].search([('is_default_consumption','=',True)],limit=1)
    #     # if def_site:
    #     #     res['site_name'] = def_site.id
    #     return res

class InventoryLineInherit(models.Model):
    _inherit = "stock.inventory.line"

    #This field commented by vivek. It was added by your previous developer.
    #But, it should not be like this.
    # theoretical_qty = fields.Float('Theoretical Quantity', readonly=False,store=True,default=0.0,compute=False)
    
    #This field is added by vivek. Its as it as like the base field. 
    theoretical_qty = fields.Float(
        'Theoretical Quantity', compute='_compute_theoretical_qty',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True, store=True)


    #This function commented by Vivek. Your previous developer wrongly did it
    # @api.one
    # @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    # def _compute_theoretical_qty(self):
    #     pass
    
    #This function is added by vivek.
    #Its as same copy as like base model function of theoretical qty
    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        if not self.product_id:
            self.theoretical_qty = 0
            return
        theoretical_qty = self.product_id.get_theoretical_quantity(
            self.product_id.id,
            self.location_id.id,
            lot_id=self.prod_lot_id.id,
            package_id=self.package_id.id,
            owner_id=self.partner_id.id,
            to_uom=self.product_uom_id.id,
        )
        self.theoretical_qty = theoretical_qty
    



class StockLocation(models.Model):
    _inherit = "stock.location"


    is_default_consumption=fields.Boolean('Is Default Consumption Site')

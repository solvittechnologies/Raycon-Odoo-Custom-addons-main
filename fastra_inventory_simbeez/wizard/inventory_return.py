
from odoo import models, fields

class InventoryRequestReturn(models.TransientModel):
    _name = 'inventory.request.return'
    
    inv_req_id = fields.Many2one('inventory.request','Inventory Request')
    return_product_line_ids = fields.One2many('inventory.request.return.line', 'inventory_request_return_id', string="Lines")
    
    def action_inv_return(self):
        stock_obj = self.env['stock.move'].sudo()
        for return_line_id in self.return_product_line_ids:
            stock_move_val = {'location_id': self.inv_req_id.destination_location.id,
                              'location_dest_id': self.inv_req_id.source_location.id,
                              'product_id': return_line_id.product_id.id,
                              'product_uom': return_line_id.product_id.uom_id.id,
                              'qty_to_return': return_line_id.qty,
                              'quantity_done':return_line_id.qty,
                              'name':  self.inv_req_id.store_keeper_name.name + ': ' + return_line_id.product_id.name
                              }
            st_mv_id = stock_obj.create(stock_move_val)
            st_mv_id._action_confirm()
            st_mv_id._action_assign()
            st_mv_id._action_done()
        self.inv_req_id.write({'state_of_request': 'return'})
    
    
class InventoryRequestLineReturn(models.TransientModel):
    _name = 'inventory.request.return.line'
    
    inventory_request_return_id = fields.Many2one('inventory.request.return', string="Inventory Return")
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float("Quantity")
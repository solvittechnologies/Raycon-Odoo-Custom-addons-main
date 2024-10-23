from odoo import models, fields, api,_
from datetime import datetime

class InventoryReqConfirm(models.TransientModel):
    _name = 'inventory.confirm.req'
    
    inv_req_id = fields.Many2one('request.inventory','Inventory Request')
    expected_to_return = fields.Boolean('Expected to Return')
    
    @api.multi
    def action_inv_confirm(self):
        for record in self:
            record.inv_req_id.request_approve(record.expected_to_return)
        return
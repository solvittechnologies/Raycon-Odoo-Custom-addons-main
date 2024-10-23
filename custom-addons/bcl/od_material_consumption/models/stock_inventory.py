from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta, date


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    is_material_consumption = fields.Boolean('Material Consumption')
    material_consumption_name = fields.Char('Reference', default=_('New'))
    analytical_account = fields.Many2one('account.analytic.account')
    filter = fields.Selection(default='partial')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancle', 'Reject'),
        ('confirm', 'Approval'),
        ('done', 'Released')
    ], default='draft')


    store_keeper = fields.Many2one("res.users", String='Store Keeper',  default=lambda self: self.env.user)
    project_manager = fields.Many2one("res.users", String='Project Manager')
    partner = fields.Char()
    source_location = fields.Many2one('stock.location')
    operation_type = fields.Many2one('stock.picking.type')
    site_name = fields.Many2one('stock.location',readonly=True)
    current_user = fields.Many2one("res.users")
    # date_release = fields.Date("Request Date", default=datetime.date(datetime.now()))
    date = fields.Date("Request Date", default=datetime.date(datetime.now()))
    # request_date = fields.Date("Request Date")
    shipping_policy = fields.Selection([
        ('draft', 'Receive each product when available '),
        ('request', 'Receive all product at once'),
    ], default='draft')
    # procurement_group = fields.Char(readony=1)
    # priority = fields.Selection([
    #     ('not_urgent', 'Not urgent'),
    #     ('normal', 'Normal'),
    #     ('urgent', 'Urgent'),
    #     ('very_urgent', 'Very Urgent'),
    # ])
    product_category = fields.Many2one('product.category')
    journal_id = fields.Many2one('account.move', readonly=1)

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.current_user = self.env.user
        # i think this work too so you don't have to loop
        self.update({'current_user' : self.env.user.id})

    @api.onchange('state')
    def reduce_quantity(self):
        for rec in self:
            if rec.state == "done":
                # rec.line_ids
                for i in rec.line_ids:
                    product = self.env['product.product'].search([('id','=',i.product.id)])
                    # i.product_qty = product.qty_available
                    product.write({'qty_available':product.qty_available - i.product_qty})
                    
                    # else:
                    #     i.state = 'available'
                    #     self.write({'state': 'request'})


    @api.onchange('line_ids')
    def reduce_quantity3(self):
        for rec in self:
            for i in rec.line_ids:
                    product = self.env['product.product'].search([('id','=',i.product_id.id)])
                    i.product_qty = product.qty_available
                    i.theoretical_qty =  i.theoretical_qty

            if rec.state == "done":
                # rec.line_ids
                for i in rec.line_ids:
                    product = self.env['product.product'].search([('id','=',i.product_id.id)])
                    i.product_qty = product.qty_available

    def action_get_account_moves(self):
        form_view = self.env.ref('account.view_move_form').id
        tree_view = self.env.ref('account.view_account_move_filter').id
        get_rec = self.move_ids.ids

        return {
            'name': _('Journal Entry'),
            'domain': [('stock_move_id', 'in', get_rec)],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
        }


        self.ensure_one()
        action_data = self.env['ir.actions.act_window']._for_xml_id('account.action_move_journal_line')
        action_data['domain'] = [('id', 'in', self.stock_move_id.ids)]
        return action_data

    @api.onchange('material_consumption_name')
    def onchange_material_consumption_name(self):
        if self.is_material_consumption:
            self.name = self.material_consumption_name

    @api.model
    def create(self, vals):
        if vals.get('material_consumption_name', _('New')) == _('New'):
            vals['material_consumption_name'] = self.env['ir.sequence'].next_by_code('material.consumption.request') or _('New')
        res = super(StockInventory, self).create(vals)
        if res.is_material_consumption:
            res.name = res.material_consumption_name
        return res

    def action_open_inventory_lines(self):
        self.ensure_one()
        if self.is_material_consumption:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('od_material_consumption.stock_consumption_line_tree').id, 'tree')],
                'view_mode': 'tree',
                'name': _('Inventory Lines'),
                'res_model': 'stock.inventory.line',
            }
            context = {
                'default_is_editable': True,
                'default_inventory_id': self.id,
                'default_company_id': self.company_id.id,
            }
            # Define domains and context
            domain = [
                ('inventory_id', '=', self.id),
                ('location_id.usage', 'in', ['internal', 'transit'])
            ]
            if self.location_ids:
                context['default_location_id'] = self.location_ids[0].id
                if len(self.location_ids) == 1:
                    if not self.location_ids[0].child_ids:
                        context['readonly_location_id'] = True

            if self.product_ids:
                if len(self.product_ids) == 1:
                    context['default_product_id'] = self.product_ids[0].id

            action['context'] = context
            action['domain'] = domain
            return action
        else:
            return super(StockInventory, self).action_open_inventory_lines()


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    qty_to_consume = fields.Float('Qty to Consume')
    analytical_account = fields.Many2one('account.analytic.account',required=True)
    analytical_tag = fields.Many2one('account.analytic.tag',required=True)


    @api.model
    def create(self, vals):
        res = super(StockInventoryLine, self).create(vals)
        if vals.get('line_ids'):
            for rec in vals.get('line_ids'):
                if rec.product_id:
                    if not rec.analytical_account:
                        raise ValidationError(_("Please fill Analytical Account for product %s" %(rec.product_id.name)))
                    if not rec.analytical_tag:
                        raise ValidationError(_("Please fill Analytical Tag for product %s" %(rec.product_id.name)))
        return res

    @api.multi
    def write(self, vals):
        res = super(StockInventoryLine, self).write(vals)
        if self.line_ids:
            for rec in self.ids:
                if rec.product_id:
                    if not self.analytical_account:
                        raise ValidationError(_("Please fill Analytical Account for product %s" %(self.product_id.name)))
                    if not self.analytical_tag:
                        raise ValidationError(_("Please fill Analytical Tag for product %s"  %(self.product_id.name)))
        return res

    def _get_virtual_location(self):
        if self.inventory_id.is_material_consumption:
            return self.product_id.with_context(force_company=self.company_id.id).consumption_location_id
        return super(StockInventoryLine, self)._get_virtual_location()

    @api.onchange('qty_to_consume')
    def _compute_product_quantity(self):
        for rec in self:
            rec.product_qty = rec.theoretical_qty - rec.qty_to_consume


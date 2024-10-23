# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import random

_STATES = [
    ('draft', 'Draft'),
    ('send_to_approve', 'Send To be approved'),
    ('to_approve', 'To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('done', 'Done')
]


class AssignLocationToAccount(models.Model):
    _inherit = 'account.analytic.account'

    location = fields.Many2one('stock.location', string='Location')


class AlmMultiLocation(models.Model):
    _inherit = 'purchase.order'

    location = fields.Many2one('stock.location', string='Site Location')



    @api.multi
    def _get_destination_location(self):
        super(AlmMultiLocation,
              self)._get_destination_location()  # to overide the _get_destination_location in the purchase.order module

        self.ensure_one()
        if self.account_analytic_id.location:
            return self.account_analytic_id.location.id
        return self.picking_type_id.default_location_dest_id.id


class StoreKeeperUsers(models.Model):
    _inherit = 'stock.location'

    store_keeper = fields.Many2one('res.users', string="Location Store Keeper")
    owner_user = fields.Many2one('res.users', string="Owner User")
    branch_manager = fields.Many2one('res.users', string="Project Manager")
    branch_accountant = fields.Many2one('res.users', string="Branch Accountant")


class ButtonModification(models.Model):
    _inherit = 'stock.picking'

    def get_current_user_id(self):
        for rec in self:
            rec.current_user = rec.env.user.id

    @api.multi
    # @api.depends('location_id')
    def _check_source_location(self):
        for rec in self:
            if rec.env.user.id == rec.location_id.store_keeper.id:
                rec.source_store = True
            # print("I am true here",rec.source_store)

            else:
                rec.source_store = False
            # print("I am not true here",rec.source_store)

    @api.multi
    # @api.depends('location_dest_id')
    def _check_dest_location(self):
        for rec in self:

            if rec.env.user.id == rec.location_dest_id.store_keeper.id:
                rec.dest_store = True
            # print("THE DEBUGGING PROCESSS true",rec.dest_store)
            else:
                rec.dest_store = False
            # print("THE DEBUGGING PROCESSS false",rec.dest_store)

    @api.multi
    def _check_manager(self):
        for rec in self:
            managers = self.env.ref('stock.group_stock_manager').users
            for user in managers:
                if rec.env.user.id == user.id:
                    rec.current_manager = True
                    #print("I am true", rec.current_manager)
                    break

                else:
                    rec.current_manager = False
                    #print("I am False", rec.current_manager)

    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        # If a package level is done when confirmed its location can be different than where it will be reserved.
        # So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
        package_level_done = self.mapped('package_level_ids').filtered(lambda pl: pl.is_done and pl.state == 'confirmed')
        package_level_done.write({'is_done': False})
        moves._action_assign()
        package_level_done.write({'is_done': True})
        return True

    @api.multi
    def do_released(self):
        for rec in self:
            rec.state = 'released'


    # current_user = fields.Integer(compute = 'get_current_user_id')
    source_store = fields.Boolean(compute='_check_source_location')
    dest_store = fields.Boolean(compute='_check_dest_location')
    current_manager = fields.Boolean(compute='_check_manager')
    state = fields.Selection(selection_add=[('released', 'Released')])


class InternalTransferRequest(models.Model):
    _name = 'internal.transfer.request'
    _description = 'Internal Transfer Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.model
    def _get_approval(self):
        return self.env['res.users'].browse('stock.group_stock_manager')

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('name_seq')

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'internal'),
                                     ('warehouse_id', '=', False)])
        return types[:1]

    @api.multi
    @api.depends('state')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve', 'send_to_approve','approved', 'rejected', 'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    # print("I entered SUCCESSFULLY")
    @api.multi
    def _get_user_location(self):
        stock_owner = self._get_default_requested_by()
        flag = stock_owner.has_group('stock.group_stock_manager')
        user_location = self.env['stock.location'].search([])
        default_location = None
        for item in user_location:
            if item.partner_id.name == self.env.user.partner_id.name:
                # print("I entered SUCCESSFULLY")
                default_location = item.id
        return default_location

    @api.model
    def _get_default_location(self):
        result = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
        print(result,"result....location..")
        if len(result)==1:
            return result.id
        if len(result)>1:
            return result[0].id

    @api.depends('line_ids')
    def _compute_line_count(self):
        self.line_count = len(self.mapped('line_ids'))

    @api.multi
    def _compute_approvers(self):
        managers = self.env.ref('stock.group_stock_manager')
        # print("seniorrrrr",managers.id)
        return managers.users

    @api.model
    def _get_default_approver(self):
        result = self.env['stock.location'].search([('owner_user', '=', self.env.uid)])
        print(result.branch_manager.id,"result......")
        if len(result)>0:
            try:
                print(self.env['res.users'].browse(result.branch_manager.id).id,"kkkkkkkk")
                return result.branch_manager.id
                #return self.env['res.users'].browse(result.branch_manager.id).id
            except Exception as e:
                print("erro in assining theproject manager",e)
        if len(result)<=0:
            result_store_keeper = self.env['stock.location'].search([('store_keeper', '=', self.env.uid)])
            print(result_store_keeper,"store keeper result......")
            if result_store_keeper:
                return self.env['res.users'].browse(result_store_keeper.branch_manager.id)

    name = fields.Char('Transfer Reference', size=32,
                       track_visibility='onchange')

    #    releasing_location = fields.Many2one('stock.location','Releasing Location')

    stock_picking_ref = fields.Many2one('stock.picking', 'Stock Picking Reference')

    date_start = fields.Date('Request Date',
                             help="Date when the user initiated the "
                                  "request.",
                             default=fields.Date.context_today,
                             track_visibility='onchange')

    requested_by = fields.Many2one('res.users',
                                   'Requested By',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)

    request_location = fields.Many2one('stock.location', 'Requesting Location', default=_get_default_location,
                                       readonly=False)

    assigned_to = fields.Many2one('res.users', 'Approved By',
                                  track_visibility='onchange',default=_get_default_approver)

    description = fields.Text(string='Description')

    """company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 default=_company_get,
                                 track_visibility='onchange')"""

    line_ids = fields.One2many('internal.transfer.request.line', 'request_id',
                               'Products to Tranfer',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')

    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')

    is_editable = fields.Boolean(string="Is editable",
                                 compute="_compute_is_editable",
                                 readonly=True)

    to_approve_allowed = fields.Boolean(
        compute='_compute_to_approve_allowed')

    picking_type_id = fields.Many2one('stock.picking.type',
                                      'Picking Type', required=True,
                                      default=_default_picking_type)

    line_count = fields.Integer(
        string='Transfer Request Line Count',
        compute='_compute_line_count',
        readonly=True
    )

    """@api.multi
    def _compute_approvers(self):
	managers = self.env.ref['stock.group_stock_manager']
	print(managers.users)
	return managers.users"""

    @api.multi
    @api.depends(
        'state',
        'line_ids.product_qty',
        'line_ids.cancelled',
    )
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = (
                    rec.state == 'draft' and
                    any([
                        not line.cancelled and line.product_qty
                        for line in rec.line_ids
                    ])
            )

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self.env['ir.sequence'].next_by_code('name_seq'),
        })
        return super(InternalTransferRequest, self).copy(default)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('name_seq')
        request = super(InternalTransferRequest, self).create(vals)
        if vals.get('assigned_to'):
            self.message_subscribe(partner_ids=[request.assigned_to.id])
            # request.message_subscribe(partner_ids=[request.assigned_to.id])

        return request

    @api.multi
    def write(self, vals):
        res = super(InternalTransferRequest, self).write(vals)
        for request in self:
            if vals.get('assigned_to'):
                self.message_subscribe(partner_ids=[request.assigned_to.id])
                # self.message_subscribe_users(user_ids=[request.assigned_to.id])
        return res

    @api.multi
    def button_draft(self):
        self.mapped('line_ids').do_uncancel()
        return self.write({'state': 'draft'})


    @api.multi
    def button_send_to_approve(self):
        return self.write({'state': 'to_approve'})

    @api.multi
    def button_to_approve(self):
        self.to_approve_allowed_check()
        for line in self.line_ids:
            line.state = 'send_to_approve'
        return self.write({'state': 'send_to_approve'})

    @api.multi
    def button_approved(self):
        uniqueList = []
        locExist = True;
        for rec in self.line_ids:
            for loc in rec.releasing_location:
                locExist = False
                for x in uniqueList:
                    if x == loc:
                        locExist = True
                        break
            if not locExist:
                # print(loc)
                self._create_picking(loc.id)
                uniqueList.append(loc)
        self.assigned_to = self.env.user.id
        return self.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        self.mapped('line_ids').do_cancel()
        return self.write({'state': 'rejected'})

    @api.multi
    def button_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def check_auto_reject(self):
        """When all lines are cancelled the transfer request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({'state': 'rejected'})

    @api.multi
    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(
                    _("You can't request an approval for a transfer request "
                      "which is empty. (%s)") % rec.name)

    @api.multi
    def _prepare_lines(self, picking, loc):
        line_ids = []
        for rec in self:
            for line in rec.line_ids:
                if line.releasing_location.id == loc:
                    self.env['stock.move'].create({
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.product_qty,
                        'location_dest_id': rec.request_location.id,
                        'picking_id': picking.id,
                        # 'location_id': rec.releasing_location.id,
                        'location_id': line.releasing_location.id,
                        'date_expected': self.date_start,
                        'product_uom': line.product_uom_id.id
                    })
        return line_ids

    # return {
    #   'product_id':self.line_ids.product_id,
    #  'name':self.line_ids.name,
    #  'product_uom_qty':self.line_ids.product_qty,
    # }
    @api.multi
    def _prepare_picking(self, loc):
        """if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.requested_by.id
            })"""
        # if not self.releasing_location.id:
        #     raise UserError(_("Please select a Releasing location"))
        return {
            'name': self.name + str(loc) + str(random.randint(0, 22)),
            'partner_id': self.requested_by.partner_id.id,
            'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal')])[:1].id,
            'picking_type_code': 'internal',
            'date': self.date_start,
            'origin': self.name,
            'location_dest_id': self.request_location.id,
            # 'location_id': self.releasing_location.id,
            'location_id': loc,
            'company_id': self.env.user.company_id.id,

        }

    @api.multi
    def _create_picking(self, loc):
        StockPicking = self.env['stock.picking']
        for order in self:
            res = order._prepare_picking(loc)
            picking = StockPicking.create(res)
            # create move lines here
            move = self._prepare_lines(picking, loc)
            # save reference to stock picking on internal transfer
            picking.action_confirm()
            order.stock_picking_ref = picking
        return picking
    @api.multi
    def action_view_purchase_request_line(self):


        return {
            'name': _('Lines'),
            'domain': [('id', 'in', self.line_ids.ids),],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
            'res_model': 'internal.transfer.request.line',
            'type': 'ir.actions.act_window',
        }


class TransferRequestLine(models.Model):
    _name = "internal.transfer.request.line"
    _description = "Internal Transfer Request Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'send_to_approve', 'approved', 'rejected',
                                        'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    """@api.multi
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name"""

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)],
        track_visibility='onchange')

    name = fields.Char('Description', size=256,
                       track_visibility='onchange')

    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')

    product_qty = fields.Float('Quantity', track_visibility='onchange',
                               digits=dp.get_precision(
                                   'Product Unit of Measure'))

    request_id = fields.Many2one('internal.transfer.request',
                                 'Transfer Request',
                                 ondelete='cascade', readonly=True)

    releasing_location = fields.Many2one('stock.location', 'Releasing Location')

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange', required=True)

    analytic_tag = fields.Many2one('account.analytic.tag', 'Analytic Tag')

    requested_by = fields.Many2one('res.users',
                                   related='request_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)

    assigned_to = fields.Many2one('res.users',
                                  related='request_id.assigned_to',
                                  string='Assigned to',
                                  store=True, readonly=True)

    date_start = fields.Date(related='request_id.date_start',
                             store=True, readonly=True)

    description = fields.Text(related='request_id.description',
                              string='Description', readonly=True,
                              store=True)

    """origin = fields.Char(related='request_id.origin',
                         size=32, string='Source Document', readonly=True,
                         store=True)"""

    date_required = fields.Date(string='Request Date', required=True,
                                track_visibility='onchange',
                                default=fields.Date.context_today)

    is_editable = fields.Boolean(string='Is editable',
                                 compute="_compute_is_editable",
                                 readonly=True)

    specifications = fields.Text(string='Specifications')

    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)

    cancelled = fields.Boolean(
        string="Cancelled", readonly=True, default=False, copy=False)


    state = fields.Selection(selection=_STATES,
                             string='Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft')



    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name

    @api.multi
    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({'cancelled': True})

    @api.multi
    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({'cancelled': False})

    @api.multi
    def write(self, vals):
        res = super(TransferRequestLine, self).write(vals)
        if vals.get('cancelled'):
            requests = self.mapped('request_id')
            requests.check_auto_reject()
        return res


class StockPickinInherited(models.Model):
    _inherit = "stock.picking"

    # location_id = fields.Many2one()
    # location_id = fields.Many2one()

    @api.multi
    def do_new_transfer(self):
        print(self.origin, "origin is here")
        if self.origin:
            internal_transfer_obj = []
            if 'IR' in self.origin:
                internal_transfer_obj = self.env['internal.transfer.request'].search([('name', '=', self.origin)])[0]
                print(internal_transfer_obj)
            if internal_transfer_obj:
                internal_transfer_obj.write({'state': 'done'})
        return super(StockPickinInherited, self).do_new_transfer()

    @api.model
    def get_current_location(self):
        for rec in self:

            rec.location_id = self.env['stock.location'].search([('id', '=', 18)]).id
            rec.location_dest_id = self.env['stock.location'].search([('id', '=', 18)]).id

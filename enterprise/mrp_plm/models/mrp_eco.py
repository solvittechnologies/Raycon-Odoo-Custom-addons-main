# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError


class MrpEcoType(models.Model):
    _name = "mrp.eco.type"
    _description = 'Manufacturing Process'
    _inherit = ['mail.alias.mixin', 'mail.thread']

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence')
    alias_id = fields.Many2one('mail.alias', 'Alias', ondelete='restrict', required=True)
    nb_ecos = fields.Integer('ECOs', compute='_compute_nb')
    nb_approvals = fields.Integer('Waiting Approvals', compute='_compute_nb')
    nb_approvals_my = fields.Integer('Waiting my Approvals', compute='_compute_nb')
    nb_validation = fields.Integer('To Apply', compute='_compute_nb')
    color = fields.Integer('Color')
    stage_ids = fields.One2many('mrp.eco.stage', 'type_id', 'Stages')

    @api.one
    def _compute_nb(self):
        # TDE FIXME: this seems not good for performances, to check (replace by read_group later on)
        MrpEco = self.env['mrp.eco']
        for eco_type in self:
            eco_type.nb_ecos = MrpEco.search_count([('type_id', '=', eco_type.id)])
            eco_type.nb_validation = MrpEco.search_count([('stage_id.type_id', '=', eco_type.id), ('stage_id.allow_apply_change', '=', True), ('state', '=', 'progress')])
            eco_type.nb_approvals = MrpEco.search_count([('stage_id.type_id', '=', eco_type.id), ('approval_ids.status', '=', 'none')])
            eco_type.nb_approvals_my = MrpEco.search_count([('stage_id.type_id', '=', eco_type.id), ('approval_ids.status', '=', 'none'), 
                                                       ('approval_ids.required_user_ids', '=', self.env.user.id)])

    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'mrp.eco')

    def get_alias_values(self):
        values = super(MrpEcoType, self).get_alias_values()
        values['alias_defaults'] = {'type_id': self.id}
        return values


class MrpEcoApprovalTemplate(models.Model):
    _name = "mrp.eco.approval.template"
    _order = "sequence"

    name = fields.Char('Role', required=True)
    sequence = fields.Integer('Sequence')
    approval_type = fields.Selection([
        ('optional', 'Approves, but the approval is optional'),
        ('mandatory', 'Is required to approve'),
        ('comment', 'Comments only')], 'Approval Type',
        default='mandatory', required=True)
    user_ids = fields.Many2many('res.users', string='Users', required=True)
    stage_id = fields.Many2one('mrp.eco.stage', 'Stage', required=True)


class MrpEcoApproval(models.Model):
    _name = "mrp.eco.approval"

    eco_id = fields.Many2one(
        'mrp.eco', 'ECO',
        ondelete='cascade', required=True)
    approval_template_id = fields.Many2one(
        'mrp.eco.approval.template', 'Template',
        ondelete='cascade', required=True)
    name = fields.Char('Role', related='approval_template_id.name', store=True)
    user_id = fields.Many2one(
        'res.users', 'Approved by')
    required_user_ids = fields.Many2many(
        'res.users', string='Requested Users', related='approval_template_id.user_ids')
    template_stage_id = fields.Many2one(
        'mrp.eco.stage', 'Approval Stage',
        related='approval_template_id.stage_id', store=True)
    eco_stage_id = fields.Many2one(
        'mrp.eco.stage', 'ECO Stage',
        related='eco_id.stage_id', store=True)
    status = fields.Selection([
        ('none', 'Not Yet'),
        ('comment', 'Commented'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')], string='Status',
        default='none', required=True)
    is_approved = fields.Boolean(
        compute='_compute_is_approved', store=True)
    is_rejected = fields.Boolean(
        compute='_compute_is_rejected', store=True)

    @api.one
    @api.depends('status', 'approval_template_id.approval_type')
    def _compute_is_approved(self):
        if self.approval_template_id.approval_type == 'mandatory':
            self.is_approved = self.status == 'approved'
        else:
            self.is_approved = True

    @api.one
    @api.depends('status', 'approval_template_id.approval_type')
    def _compute_is_rejected(self):
        if self.approval_template_id.approval_type == 'mandatory':
            self.is_rejected = self.status == 'rejected'
        else:
            self.is_rejected = False


class MrpEcoStage(models.Model):
    _name = 'mrp.eco.stage'
    _description = 'Engineering Change Order Stage'
    _order = "sequence, id"
    _fold_name = 'folded'

    def _default_sequence(self):
        last_stage = self.search([], order='sequence DESC', limit=1)
        return 1 + (last_stage.sequence or 0)

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=lambda s: s._default_sequence())
    folded = fields.Boolean('Folded in kanban view')
    allow_apply_change = fields.Boolean('Final Stage')
    type_id = fields.Many2one('mrp.eco.type', 'Type', required=True, default=lambda self: self.env['mrp.eco.type'].search([], limit=1))
    approval_template_ids = fields.One2many('mrp.eco.approval.template', 'stage_id', 'Approvals')
    approval_roles = fields.Char('Approval Roles', compute='_compute_approvals', store=True)
    is_blocking = fields.Boolean('Blocking Stage', compute='_compute_is_blocking', store=True)

    @api.one
    @api.depends('approval_template_ids.name')
    def _compute_approvals(self):
        self.approval_roles = ', '.join(self.approval_template_ids.mapped('name'))

    @api.one
    @api.depends('approval_template_ids.approval_type')
    def _compute_is_blocking(self):
        self.is_blocking = any(template.approval_type == 'mandatory' for template in self.approval_template_ids)


class MrpEco(models.Model):
    _name = 'mrp.eco'
    _description = 'Engineering Change Order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Reference', copy=False, required=True)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    type_id = fields.Many2one('mrp.eco.type', 'Type', required=True)
    stage_id = fields.Many2one(
        'mrp.eco.stage', 'Stage', copy=False, domain="[('type_id', '=', type_id)]",
        group_expand='_read_group_stage_ids',
        default=lambda self: self.env['mrp.eco.stage'].search([('type_id', '=', self._context.get('default_type_id'))], limit=1))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    tag_ids = fields.Many2many('mrp.eco.tag', string='Tags')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')], string='Priority',
        index=True)
    note = fields.Text('Note')
    effectivity = fields.Selection([
        ('asap', 'As soon as possible'),
        ('date', 'At Date')], string='Effectivity',  # Is this English ?
        default='asap', required=True)  # TDE: usefull ?
    effectivity_date = fields.Datetime('Effectivity Date')
    approval_ids = fields.One2many('mrp.eco.approval', 'eco_id', 'Approvals')

    state = fields.Selection([
        ('confirmed', 'To Do'),
        ('progress', 'In Progress'),
        ('done', 'Done')], string='Status',
        copy=False, default='confirmed', readonly=True, required=True)
    user_can_approve = fields.Boolean(
        'Can Approve', compute='_compute_user_can_approve',
        help='Technical field to check if approval by current user is required')
    user_can_reject = fields.Boolean(
        'Can Reject', compute='_compute_user_can_reject',
        help='Technical field to check if reject by current user is possible')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Approved'),
        ('blocked', 'Blocked')], string='Kanban State',
        copy=False, compute='_compute_kanban_state', store=True)
    allow_change_stage = fields.Boolean(
        'Allow Change Stage', compute='_compute_allow_change_stage')
    allow_apply_change = fields.Boolean(
        'Show Apply Change', compute='_compute_allow_apply_change')

    product_tmpl_id = fields.Many2one('product.template', "Product")
    type = fields.Selection([
        ('bom', 'Bill of Materials'),
        ('routing', 'Routing'),
        ('both', 'BoM and Routing')], string='Apply on',
        default='bom', required=True)
    bom_id = fields.Many2one(
        'mrp.bom', "Bill of Materials",
        domain="[('product_tmpl_id', '=', product_tmpl_id)]")  # Should at least have bom or routing on which it is applied?
    new_bom_id = fields.Many2one(
        'mrp.bom', 'New Bill of Materials',
        copy=False)
    new_bom_revision = fields.Integer('BoM Revision', related='new_bom_id.version', store=True)
    routing_id = fields.Many2one('mrp.routing', "Routing")
    new_routing_id = fields.Many2one(
        'mrp.routing', 'New Routing',
        copy=False)
    new_routing_revision = fields.Integer('Routing Revision', related='new_routing_id.version', store=True)
    bom_change_ids = fields.One2many(
        'mrp.eco.bom.change', 'eco_id', string="ECO BoM Changes",
        compute='_compute_bom_change_ids', store=True)
    routing_change_ids = fields.One2many(
        'mrp.eco.routing.change', 'eco_id', string="ECO Routing Changes",
        compute='_compute_routing_change_ids', store=True)

    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id', string='Attachments',
        auto_join=True, domain=lambda self: [('res_model', '=', self._name)])
    displayed_image_id = fields.Many2one(
        'ir.attachment', 'Displayed Image',
        domain="[('res_model', '=', 'mrp.eco'), ('res_id', '=', id), ('mimetype', 'ilike', 'image')]")
    color = fields.Integer('Color')

    @api.one
    @api.depends('bom_id.bom_line_ids', 'new_bom_id.bom_line_ids')
    def _compute_bom_change_ids(self):
        # TDE TODO: should we add workcenter logic ?
        new_bom_commands = []
        old_bom_lines = dict(((line.product_id, line.product_uom_id, tuple(line.attribute_value_ids.ids),), line) for line in self.bom_id.bom_line_ids)
        if self.new_bom_id and self.bom_id:
            for line in self.new_bom_id.bom_line_ids:
                key = (line.product_id, line.product_uom_id, tuple(line.attribute_value_ids.ids),)
                old_line = old_bom_lines.pop(key, None)
                if old_line and tools.float_compare(old_line.product_qty, line.product_qty, line.product_uom_id.rounding) != 0:
                    new_bom_commands += [(0, 0, {
                        'change_type': 'update',
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'new_product_qty': line.product_qty,
                        'old_product_qty': old_line.product_qty})]
                elif not old_line:
                    new_bom_commands += [(0, 0, {
                        'change_type': 'add',
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'new_product_qty': line.product_qty
                    })]
            for key, old_line in old_bom_lines.iteritems():
                new_bom_commands += [(0, 0, {
                    'change_type': 'remove',
                    'product_id': old_line.product_id.id,
                    'product_uom_id': old_line.product_uom_id.id,
                    'old_product_qty': old_line.product_qty,
                })]
        self.bom_change_ids = new_bom_commands

    @api.one
    @api.depends('routing_id.operation_ids', 'new_routing_id.operation_ids')
    def _compute_routing_change_ids(self):
        # TDE TODO: should we add workcenter logic ?
        new_routing_commands = []
        old_routing_lines = dict(((op.workcenter_id,), op) for op in self.routing_id.operation_ids)
        if self.new_routing_id and self.routing_id:
            for operation in self.new_routing_id.operation_ids:
                key = (operation.workcenter_id,)
                old_op = old_routing_lines.pop(key, None)
                if old_op and tools.float_compare(old_op.time_cycle_manual, operation.time_cycle_manual, 2) != 0:
                    new_routing_commands += [(0, 0, {
                        'change_type': 'update',
                        'workcenter_id': operation.workcenter_id.id,
                        'new_time_cycle_manual': operation.time_cycle_manual,
                        'old_time_cycle_manual': old_op.time_cycle_manual
                    })]
                elif not old_op:
                    new_routing_commands += [(0, 0, {
                        'change_type': 'add',
                        'workcenter_id': operation.workcenter_id.id,
                        'new_time_cycle_manual': operation.time_cycle_manual
                    })]
            for key, old_op in old_routing_lines.iteritems():
                new_routing_commands += [(0, 0, {
                    'change_type': 'remove',
                    'workcenter_id': old_op.workcenter_id.id,
                    'old_time_cycle_manual': old_op.time_cycle_manual
                })]
        self.routing_change_ids = new_routing_commands

    @api.multi
    @api.depends('approval_ids')
    def _compute_user_can_approve(self):
        approvals = self.env['mrp.eco.approval'].search([
            ('eco_id', 'in', self.ids),
            ('status', 'not in', ['approved']),
            ('template_stage_id', 'in', self.mapped('stage_id').ids),
            ('approval_template_id.approval_type', 'in', ('mandatory', 'optional')),
            ('required_user_ids', 'in', self.env.uid)])
        to_approve_eco_ids = approvals.mapped('eco_id').ids
        for eco in self:
            self.user_can_approve = eco.id in to_approve_eco_ids

    @api.multi
    @api.depends('approval_ids')
    def _compute_user_can_reject(self):
        approvals = self.env['mrp.eco.approval'].search([
            ('eco_id', 'in', self.ids),
            ('status', 'not in', ['rejected']),
            ('template_stage_id', 'in', self.mapped('stage_id').ids),
            ('approval_template_id.approval_type', 'in', ('mandatory', 'optional')),
            ('required_user_ids', 'in', self.env.uid)])
        to_reject_eco_ids = approvals.mapped('eco_id').ids
        for eco in self:
            self.user_can_reject = eco.id in to_reject_eco_ids

    @api.one
    @api.depends('approval_ids.is_approved', 'approval_ids.is_rejected')
    def _compute_kanban_state(self):
        """ State of ECO is based on the state of approvals for the current stage. """
        approvals = self.approval_ids.filtered(lambda app: app.template_stage_id == self.stage_id)
        if not approvals:
            self.kanban_state = 'normal'
        elif all(approval.is_approved for approval in approvals):
            self.kanban_state = 'done'
        elif any(approval.is_rejected for approval in approvals):
            self.kanban_state = 'blocked'
        else:
            self.kanban_state = 'normal'

    @api.one
    @api.depends('kanban_state', 'stage_id', 'approval_ids')
    def _compute_allow_change_stage(self):
        approvals = self.approval_ids.filtered(lambda app: app.template_stage_id == self.stage_id)
        if approvals:
            self.allow_change_stage = self.kanban_state == 'done'
        else:
            self.allow_change_stage = self.kanban_state in ['normal', 'done']

    @api.one
    @api.depends('state', 'stage_id.allow_apply_change')
    def _compute_allow_apply_change(self):
        self.allow_apply_change = self.stage_id.allow_apply_change and self.state in ('confirmed', 'progress')

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id.bom_ids:
            self.bom_id = self.product_tmpl_id.bom_ids.ids[0]

    @api.onchange('bom_id', 'type')
    def onchange_bom_id(self):
        if self.type == 'both':
            self.routing_id = self.bom_id.routing_id

    @api.onchange('type_id')
    def onchange_type_id(self):
        self.stage_id = self.env['mrp.eco.stage'].search([('type_id', '=', self.type_id.id)], limit=1).id

    @api.model
    def create(self, vals):
        prefix = self.env['ir.sequence'].next_by_code('mrp.eco') or ''
        vals['name'] = '%s%s' % (prefix and '%s: ' % prefix or '', vals.get('name', ''))
        eco = super(MrpEco, self).create(vals)
        eco._create_approvals()
        return eco

    @api.multi
    def write(self, vals):
        if vals.get('stage_id'):
            if any(not eco.allow_change_stage for eco in self):
                raise UserError(_('You cannot change the stage, as approvals are still required.'))
            new_stage = self.env['mrp.eco.stage'].browse(vals['stage_id'])
            minimal_sequence = min(self.mapped('stage_id').mapped('sequence'))
            has_blocking_stages = self.env['mrp.eco.stage'].search_count([
                ('sequence', '>=', minimal_sequence),
                ('sequence', '<=', new_stage.sequence),
                ('type_id', 'in', self.mapped('type_id').ids),
                ('id', 'not in', self.mapped('stage_id').ids + [vals['stage_id']]),
                ('is_blocking', '=', True)])
            if has_blocking_stages:
                raise UserError(_('You cannot change the stage, as approvals are required in the process.'))
        res = super(MrpEco, self).write(vals)
        if vals.get('stage_id'):
            self._create_approvals()
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages of the ECO type
        in the Kanban view, even if there is no ECO in that stage
        """
        search_domain = []
        if self._context.get('default_type_id'):
            search_domain = [('type_id', '=', self._context['default_type_id'])]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, **kwargs):
        message = super(MrpEco, self).message_post(**kwargs)
        if message.message_type == 'comment' and message.author_id == self.env.user.partner_id:
            for eco in self:
                for approval in eco.approval_ids.filtered(lambda app: app.template_stage_id == self.stage_id and app.status == 'none'):
                    if self.env.user in approval.approval_template_id.user_ids:
                        approval.write({
                            'status': 'comment',
                            'user_id': self.env.uid
                        })
        return message

    @api.multi
    def _create_approvals(self):
        for eco in self:
            for approval_template in eco.stage_id.approval_template_ids:
                self.env['mrp.eco.approval'].create({
                    'eco_id': eco.id,
                    'approval_template_id': approval_template.id,
                })

    @api.multi
    def approve(self):
        for eco in self:
            for approval in eco.approval_ids.filtered(lambda app: app.template_stage_id == self.stage_id and app.approval_template_id.approval_type in ('mandatory', 'optional')):
                if self.env.user in approval.approval_template_id.user_ids:
                    approval.write({
                        'status': 'approved',
                        'user_id': self.env.uid
                    })

    @api.multi
    def reject(self):
        for eco in self:
            for approval in eco.approval_ids.filtered(lambda app: app.template_stage_id == self.stage_id and app.approval_template_id.approval_type in ('mandatory', 'optional')):
                if self.env.user in approval.approval_template_id.user_ids:
                    approval.write({
                        'status': 'rejected',
                        'user_id': self.env.uid
                    })

    @api.multi
    def action_new_revision(self):
        IrAttachment = self.env['ir.attachment']  # FORWARDPORT UP TO SAAS-15
        for eco in self:
            if eco.type in ('bom', 'both'):
                eco.new_bom_id = eco.bom_id.copy(default={
                    'name': eco.bom_id.product_tmpl_id.name,
                    'version': eco.bom_id.version + 1,
                    'active': False,
                    'previous_bom_id': eco.bom_id.id,
                })
                attachments = IrAttachment.search([('res_model', '=', 'mrp.bom'),
                                                   ('res_id', '=', eco.bom_id.id)])
                for attachment in attachments:
                    attachment.copy(default={'res_id':eco.new_bom_id.id})
            if eco.type in ('routing', 'both'):
                eco.new_routing_id = eco.routing_id.copy(default={
                    'version': eco.routing_id.version + 1,
                    'active': False,
                    'previous_routing_id': eco.routing_id.id
                }).id
                attachments = IrAttachment.search([('res_model', '=', 'mrp.routing'),
                                                   ('res_id', '=', eco.routing_id.id)])
                for attachment in attachments:
                    attachment.copy(default={'res_id':eco.new_routing_id.id})
            if eco.type == 'both':
                eco.new_bom_id.routing_id = eco.new_routing_id.id
                for line in eco.new_bom_id.bom_line_ids:
                    line.operation_id = eco.new_routing_id.operation_ids.filtered(lambda x: x.name == line.operation_id.name).id
        self.write({'state': 'progress'})

    @api.multi
    def action_apply(self):
        self.mapped('new_bom_id').apply_new_version()
        self.mapped('new_routing_id').apply_new_version()
        self.write({'state': 'done'})

    @api.multi
    def action_create_alert(self):
        self.ensure_one()
        return {
            'name': _('Workorder Messages'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.message',
            'view_id': self.env.ref('mrp.mrp_message_view_form_embedded_bom').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_product_id': self.env['product.product'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)], limit=1).id,
                'default_routing_id': self.routing_id.id,
                'default_bom_id': self.bom_id.id,
                'default_message': '%s is updated or might be soon.' % self.name
            },
            'target': 'new',
        }

    @api.multi
    def open_new_bom(self):
        self.ensure_one()
        return {
            'name': _('Eco BoM'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.bom',
            'target': 'current',
            'res_id': self.new_bom_id.id}

    @api.multi
    def open_new_routing(self):
        self.ensure_one()
        return {
            'name': _('Eco Routing'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.routing',
            'target': 'current',
            'res_id': self.new_routing_id.id}


class MrpEcoBomChange(models.Model):
    _name = 'mrp.eco.bom.change'
    _description = 'ECO Material changes'

    eco_id = fields.Many2one('mrp.eco', 'Engineering Change', ondelete='cascade', required=True)
    change_type = fields.Selection([('add', 'Add'), ('remove', 'Remove'), ('update', 'Update')], string='Type', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_id = fields.Many2one('product.uom', 'Product  UoM', required=True)
    old_product_qty = fields.Float('Previous revision quantity', default=0)
    new_product_qty = fields.Float('New revision quantity', default=0)
    upd_product_qty = fields.Float('Quantity', compute='_compute_upd_product_qty', store=True)

    @api.one
    @api.depends('new_product_qty', 'old_product_qty')
    def _compute_upd_product_qty(self):
        self.upd_product_qty = self.new_product_qty - self.old_product_qty


class MrpEcoRoutingChange(models.Model):
    _name = 'mrp.eco.routing.change'
    _description = 'Eco Routing changes'

    eco_id = fields.Many2one('mrp.eco', 'Engineering Change', ondelete='cascade', required=True)
    change_type = fields.Selection([('add', 'Add'), ('remove', 'Remove'), ('update', 'Update')], string='Type', required=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center')
    old_time_cycle_manual = fields.Float('Old manual duration', default=0)
    new_time_cycle_manual = fields.Float('New manual duration', default=0)
    upd_time_cycle_manual = fields.Float('Manual Duration Change', compute='_compute_upd_time_cycle_manual', store=True)

    @api.one
    @api.depends('new_time_cycle_manual', 'old_time_cycle_manual')
    def _compute_upd_time_cycle_manual(self):
        self.upd_time_cycle_manual = self.new_time_cycle_manual - self.old_time_cycle_manual


class MrpEcoTag(models.Model):
    _name = "mrp.eco.tag"
    _description = "ECO Tags"

    name = fields.Char(required=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

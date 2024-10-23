# -*- coding: utf-8 -*-

from odoo import models, fields, api ,_
from odoo.exceptions import UserError


class ProjectCost(models.Model):
    _name = 'project_cost.project_cost'
    _description = 'project_costing.project_costing'

    name = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('Approve', 'Approve'),
        ('Confirm', 'Finalized'),
        # ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
    )
    project_manager = fields.Many2one('res.partner')
    cost_of_boq = fields.Float('',compute='_compute_cost_of_boq', store=True)

    project_id = fields.Many2one('project.project', string='Project')

    #employees = fields.One2many('res.users', 'project', string='Resource')

    budget = fields.One2many('project.budget', 'cost', string="budget")

    material = fields.One2many('project.material', 'project', string="Material")
    plant = fields.One2many('project.plant', 'project', string="Plants")
    expenses = fields.One2many('project.expenses', 'project', string="Expenses")
    #labour = fields.One2many('project.labour', 'project', string="Labour")
    subcontract = fields.One2many('project.subcontract', 'project', string="Subcontract")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")

    actual_amount = fields.Float('', )
    estimated_amount = fields.Float()
    difference = fields.Float('', compute='_compute_difference', store=True)
    # material_amount = fields.Float(String="Budget Amount")
    actual_cost = fields.Float('', compute='_compute_actual_cost', store=True)
    net_value = fields.Float('', compute='_compute_net_value', store=True)

    # expenses_amount = fields.Float()
    # subcontract_amount = fields.Float()

    target_cost = fields.Float(String="Total Target Cost", compute='_compute_target_cost', store=True)

    @api.depends('budget', )
    def _compute_target_cost(self):
        target_cost = 0.0
        for rec in self:
            for budget in rec.budget:
                target_cost += budget.target_cost
                rec.target_cost = target_cost
        return target_cost


    @api.depends('budget',)
    def _compute_actual_cost(self):
        actual_cost = 0.0
        for rec in self:
            for budget in rec.budget:
                actual_cost += budget.actual_cost
                rec.actual_cost = actual_cost
        return actual_cost

    @api.depends('budget',)
    def _compute_cost_of_boq(self):
        cost_of_boq = 0.0
        for rec in self:
            for budget in rec.budget:
                cost_of_boq += budget.cost_qob_amount
                rec.cost_of_boq = cost_of_boq
        return cost_of_boq

    @api.depends('target_cost', 'actual_cost',)
    def _compute_net_value(self):
        net_value = 0.0
        for rec in self:
            net_value = rec.target_cost - rec.actual_cost
            rec.net_value = abs(net_value)
        return net_value

    @api.depends('target_cost', 'actual_amount',)
    def _compute_difference(self):
        difference = 0.0
        for rec in self:
            difference = rec.target_cost - rec.actual_amount
            rec.difference = abs(difference)
        return difference

    def submit_request(self):
        for rec in self:
            rec.write({'state': 'request'})

    def approve(self):

        new_po = self.env['purchase.order']
        for rec in self:
            rec.write({'state': 'Approve'})

    def finalize(self):
        for rec in self:
            rec.write({'state': 'Confirm'})


class ProjectElementCategory(models.Model):
    _name = 'project.element.category'
    _description = 'ProjectElementCategory'
    name = fields.Char()


class ProjectElement(models.Model):
    _name = 'project.element'
    _description = 'ProjectElement'
    name = fields.Char('')
    category = fields.Many2one('project.element.category', string='', )


class ProjectBudget(models.Model):
    _name = 'project.budget'
    _description = 'ProjectBudget'
    rec_name = 'element'

    cost = fields.Many2one(
        comodel_name='project_cost.project_cost',
        string='Project Cost', )
    element_no = fields.Char('')
    category = fields.Many2one('project.element.category', string='', )
    element = fields.Many2one('project.element', String="Element")
    item = fields.Char(
        string='Item', )
    description = fields.Text(String="Description")
    quantity = fields.Float(String="Quantity")
    unit = fields.Char(
        string='Unit', )
    cost_qob_rate = fields.Float(String="")
    cost_qob_amount = fields.Float(String="")
    material_rate = fields.Float(String="")
    material_amount = fields.Float(String="")
    labour_rate = fields.Float(String="")
    labour_amount = fields.Float(String="")
    plant_rate = fields.Float(String="")
    plant_amount = fields.Float(String="")
    subcontractor_amount = fields.Float(String="")
    target_cost = fields.Float(String="", compute='_compute_target_cost', store=True)
    actual_cost = fields.Float()
    net_value = fields.Float('', compute='_compute_net_value', store=True)

    @api.depends('cost_qob_amount', 'material_amount', 'labour_amount', 'plant_amount', 'subcontractor_amount')
    def _compute_target_cost(self):
        target_cost = 0.0
        for rec in self:
            target_cost = rec.cost_qob_amount + rec.material_amount + rec.labour_amount + rec.plant_amount + rec.subcontractor_amount
            rec.target_cost = target_cost
        return target_cost

    @api.depends('target_cost', 'actual_cost',)
    def _compute_net_value(self):
        net_value = 0.0
        for rec in self:
            net_value = rec.target_cost - rec.actual_cost
            rec.net_value = abs(net_value)
        return net_value

class ProjectLabour(models.Model):
    _name = 'project.labour'
    _description = 'ProjectLabour'
    _rec_name = 'project_id'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait_approve', 'Wait Approve'),
        ('Approve', 'Approve'),

    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
    )

    project_id = fields.Many2one('project.project', string='Project')
    project_manager = fields.Many2one('res.partner')
    date = fields.Date(string='Date')
    week = fields.Char(string='Week')
    headman_rate = fields.Float(string='')
    skilled_rate = fields.Float(string='')
    unskilled_rate = fields.Float(string='')
    semi_skilled_rate = fields.Float(string='')
    labour_cost = fields.One2many(
        comodel_name='project.labour.cost',
        inverse_name='project_labour',
        string='',)
    total_labour_cost = fields.Float(String="Total Labour cost", compute='_compute_total_labour_cost', store=True)
    def submit_request(self):
        for rec in self:
            rec.write({'state': 'wait_approve'})

    def approve(self):
        for rec in self:
            rec.write({'state': 'Approve'})



    @api.depends('labour_cost',)
    def _compute_total_labour_cost(self):
        labour_cost = 0.0
        for rec in self:
            for line in rec.labour_cost:
                labour_cost += line.total_labour_cost
                rec.total_labour_cost = labour_cost
        return labour_cost

class ProjectLabourCost(models.Model):
    _name = 'project.labour.cost'
    _description = 'ProjectLabourCost'

    project_labour = fields.Many2one(
        comodel_name='project.labour',
        string='')
    description = fields.Text(String="Work Task Description")
    element = fields.Many2one('project.element', String="Element")
    trade = fields.Many2one('project.trade', "TRADE")
    hrs_worked = fields.Float(String="NO OF HRS WORKED")
    head_foreman = fields.Float(String="Head Foreman Men")
    skilled = fields.Float(String="Skilled Men")
    semi_skilled = fields.Float(String="Semi-Skilled Men")
    unskilled = fields.Float(String="Unskilled Men")
    total_labour_cost = fields.Float(String="Total Labour cost", compute='_compute_total_labour_cost', store=True)


    @api.depends('head_foreman','skilled', 'semi_skilled','unskilled')
    def _compute_total_labour_cost(self):
        total_labour_cost = 0.0
        for rec in self:
            if rec.project_labour:
                if not rec.project_labour.headman_rate:
                    raise UserError(_('Enter Headman Rate!!!'))
                elif not rec.project_labour.skilled_rate:
                    raise UserError(_('Enter Skilled Rate!!!'))
                elif not rec.project_labour.semi_skilled_rate:
                    raise UserError(_('Enter Semi Skilled Rate!!!'))
                elif not rec.project_labour.unskilled_rate:
                    raise UserError(_('Enter  unskilled Rate!!!'))
                else:
                    headman = rec.project_labour.headman_rate * rec.head_foreman
                    skilled = rec.project_labour.skilled_rate * rec.skilled
                    semi_skilled = rec.project_labour.semi_skilled_rate * rec.semi_skilled
                    unskilled = rec.project_labour.unskilled_rate * rec.unskilled
                    total_labour_cost = headman+skilled+semi_skilled+unskilled
                    rec.total_labour_cost = total_labour_cost
            return total_labour_cost

class ProjectTrade(models.Model):
    _name = 'project.trade'
    _description = 'ProjectTrade'
    name = fields.Char()

class ProjectMaterial(models.Model):
    _name = 'project.material'
    _description = 'project_costing.project_costing'
    name = fields.Char()
    element = fields.Many2one('product.product', String="Element")
    project = fields.Many2one('project_cost.project_cost')
    description = fields.Text(String="Description")
    rate = fields.Float(String="Rate")
    quantity = fields.Float(String="Ordered Quantity")
    unit_price = fields.Float(String="Unit Price")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('display_type', self.default_get(['display_type'])['display_type']):
    #             vals.update(unit_price=0, account_id=False, quantity=0)
    #     return super(ProjectMaterial, self).create(vals_list)


class ProjectPlant(models.Model):
    _name = 'project.plant'
    _description = 'project_costing.project_costing'
    name = fields.Char()
    description = fields.Text(String="Description")
    element = fields.Many2one('product.product', String="Element")
    project = fields.Many2one('project_cost.project_cost')
    rate = fields.Float(String="Rate")
    quantity = fields.Float(String="Quantity")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")


class ProjectExpenses(models.Model):
    _name = 'project.expenses'
    _description = 'project_costing.project_costing'
    name = fields.Char()
    description = fields.Text(String="Description")
    element = fields.Many2one('product.product', String="Element")
    project = fields.Many2one('project_cost.project_cost')
    rate = fields.Float(String="Rate")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    quantity = fields.Float(String="Quantity")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")







class ProjectSubContract(models.Model):
    _name = 'project.subcontract'
    _description = 'project_costing.project_costing'
    name = fields.Char()
    description = fields.Text(String="Description")
    project = fields.Many2one('project_cost.project_cost')
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    rate = fields.Float(String="Rate")
    element = fields.Many2one('product.product', String="Element")
    quantity = fields.Float(String="Quantity")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")


class ProjectUser(models.Model):
    _inherit = 'res.users'
    project = fields.Many2one('project_cost.project_cost')


# class PurchaseReqestForm(models.Model):
#     _name = 'purchase_request_form.purchase_request_form'
#
#     project_id = fields.Many2one('project.project', string="Project Id")
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('request', 'Request'),
#         ('Approve', 'Approve'),
#         ('Confirm', 'Finalized'),
#         # ('cancel', 'Cancelled'),
#     ], string='Status', index=True, readonly=True, default='draft',
#         track_visibility='onchange', copy=False,
#     )
#     request_refrence = fields.Char('Request Refrence')
#     requested_by = fields.Many2one('res.users')
#     approved_by = fields.Many2one("res.users")
#     request_date = fields.Date('Request Date')
#     purchase_request = fields.One2many('purchase_request_form.purchase_request_line', 'element', string="Purchase Reguest")
#
#     def submit_request(self):
#         self.write({'state': 'request'})
#
#     @api.multi
#     def approve(self):
#         self.write({'state': 'Approve'})
#
#     @api.multi
#     def finalize(self):
#         self.write({'state': 'Confirm'})
#
#


class CostOfBOQ(models.Model):
    _name = 'project.costofboq'
    _description = 'Cost Of BOQ'

    name = fields.Char()
    description = fields.Text(String="Description")
    project = fields.Many2one('project_cost.project_cost')
    # rate = fields.Float(String="Rate")
    boq_lines = fields.One2many('project.costofboqline', 'project_cost', String="Element")
    # quantity = fields.Float(String="Quantity")
    amount = fields.Float(String="Amount")
    # budget_amount = fields.Float(String="Budget Amount")


class CostOfBOQLine(models.Model):
    _name = 'project.costofboqline'
    _description = 'Cost Of BOQ'

    project_cost = fields.Many2one('project.costofboq', '')
    element = fields.Many2one('product.product')
    quantity = fields.Float(String="Quantity")
    unit = fields.Float(String="Unit")
    rate = fields.Float(String="Rate")
    amount = fields.Float(String="Amount")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")
    description = fields.Text('Description')

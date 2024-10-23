# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
    cost_of_boq = fields.Float()

    project_id = fields.Many2one('project.project', string='Project')

    employees = fields.One2many('res.users', 'project', string='Resource')

    material = fields.One2many('project.material', 'project', string="Material")
    plant = fields.One2many('project.plant', 'project', string="Plants")
    expenses = fields.One2many('project.expenses', 'project', string="Expenses")
    labour = fields.One2many('project.labour', 'project', string="Labour")
    subcontract = fields.One2many('project.subcontract', 'project', string="Subcontract")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")

    actual_amount = fields.Float()
    estimated_amount = fields.Float()
    difference = fields.Float()
    # material_amount = fields.Float(String="Budget Amount")
    budget_amount = fields.Float()
    # expenses_amount = fields.Float()
    # subcontract_amount = fields.Float()

    @api.multi
    def submit_request(self):
        self.write({'state': 'request'})

    @api.multi
    def approve(self):
        new_po = self.env['purchase.order']

        jkdsksdcksjd
        self.write({'state': 'Approve'})

    @api.multi
    def finalize(self):
        self.write({'state': 'Confirm'})


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


class ProjectLabour(models.Model):
    _name = 'project.labour'
    _description = 'project_costing.project_costing'
    name = fields.Char()
    description = fields.Text(String="Description")
    project = fields.Many2one('project_cost.project_cost')
    rate = fields.Float(String="Rate")
    analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
    quantity = fields.Float(String="Quantity")
    element = fields.Many2one('product.product', String="Element")
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
# class PurchaseRequestLine(models.Model):
#     _name = 'purchase_request_form.purchase_request_line'
#
#     phases = fields.Char('phases')
#     qty = fields.Integer('Qty')
#     uom_project = fields.Float('UOM')
#     # budget_item = fields.Char('Budget Items')
#     analytical_account = fields.Many2one('account.analytic.account', string="Analytical Account")
#     element = fields.Many2one('product.product')
#     description = fields.Text('Description')


class CostOfBOQ(models.Model):
    _name = 'project.costofboq'
    _description = 'Cost Of BOQ'

    name = fields.Char()
    description = fields.Text(String="Description")
    project = fields.Many2one('project_cost.project_cost')
    # rate = fields.Float(String="Rate")
    boq_lines = fields.One2many('project.costofboqline', 'element', String="Element")
    # quantity = fields.Float(String="Quantity")
    amount = fields.Float(String="Amount")
    # budget_amount = fields.Float(String="Budget Amount")


class CostOfBOQLine(models.Model):
    _name = 'project.costofboqline'
    _description = 'Cost Of BOQ'

    element = fields.Many2one('product.product')
    quantity = fields.Float(String="Quantity")
    unit = fields.Float(String="Unit")
    rate = fields.Float(String="Rate")
    amount = fields.Float(String="Amount")
    actual_amount = fields.Float(String="Actual Amount")
    budget_amount = fields.Float(String="Budget Amount")
    description = fields.Text('Description')

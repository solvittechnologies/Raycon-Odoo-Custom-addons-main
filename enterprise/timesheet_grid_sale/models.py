# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.osv import expression

DEFAULT_INVOICED_TIMESHEET = 'all'

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_analytic(self, domain=None):
        invoice_approved_only = \
            'approved' == self.env['ir.config_parameter'].sudo().get_param(
                'sale.invoiced_timesheet', DEFAULT_INVOICED_TIMESHEET)
        if invoice_approved_only:
            domain = [
                    '&',
                        ('so_line', 'in', self.ids),
                        '|',
                            '&',
                            ('amount', '<=', 0.0),
                            ('is_timesheet', '=', False),
                            '&',
                                ('is_timesheet', '=', True),
                                ('validated', '=', True),
            ]

        return super(SaleOrderLine, self)._compute_analytic(domain=domain)


class Validation(models.TransientModel):
    _inherit = 'timesheet_grid.validation'

    @api.multi
    def validate(self):
        # As super will change the "timesheet_validated" field of a
        # "validable_employee", we have to get the min date before
        # calling super().
        validable_employees = self.validable_ids.filtered('validate').mapped('employee_id')
        oldest_last_validation_date = None
        if validable_employees:
            oldest_last_validation_date = min(validable_employees.mapped('timesheet_validated'))
        res = super(Validation, self).validate()

        # normally this would be done through a computed field, or triggered
        # by the recomputation of self.validated or something, but that does
        # not seem to be an option, and this is apparently the way to force
        # the recomputation of qty_delivered on sale_order_line
        # cf sale.sale_analytic, sale.sale.SaleOrderLine._get_to_invoice_qty
        # look for the so_line of all timesheet lines associated with the
        # same users as the validable employees (as they're all implicitly going
        # to be validated by the current validation), then recompute their
        # analytics. Semantically we should roundtrip through employee_ids,
        # but that's an o2m so (lines).mapped('user_id.employee_ids.user_id')
        # should give the same result as (lines).mapped('user_id')
        domain = expression.AND([
            [('is_timesheet', '=', True)],
            [('user_id', 'in', validable_employees.mapped('user_id').ids)]
        ])
        if oldest_last_validation_date:
            domain = expression.AND([
                domain,
                [('date','>',oldest_last_validation_date)]
            ])

        self.env['account.analytic.line'].search(domain) \
            .mapped('so_line') \
            .sudo() \
            ._compute_analytic()

        return res


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    invoiced_timesheet = fields.Selection([
        ('all', "Invoice all timesheets recorded (approved or not)"),
        ('approved', "Only invoice approved timesheets"),
    ], string="Invoice Timesheets")

    @api.multi
    def set_default_invoiced_timesheet(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                'sale.invoiced_timesheet',
                record.invoiced_timesheet
            )
        return True

    @api.model
    def get_default_invoiced_timesheet(self, fields):
        result = self.env['ir.config_parameter'].get_param('sale.invoiced_timesheet') or DEFAULT_INVOICED_TIMESHEET
        return {'invoiced_timesheet': result}

# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    allow_forecast = fields.Boolean("Allow forecast", default=False, help="This feature shows the Forecast link in the kanban view")

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            self.env['project.forecast'].with_context(active_test=False).search([('project_id', 'in', self.ids)]).write({'active': vals['active']})
        return super(Project, self).write(vals)

    @api.multi
    def create_forecast(self):
        view_id = self.env.ref('project_forecast.project_forecast_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.forecast',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {
                'default_project_id': self.id,
                'default_user_id': self.user_id.id,
            }
        }


class Task(models.Model):
    _inherit = 'project.task'

    allow_forecast = fields.Boolean('Allow Forecast', readonly=True, related='project_id.allow_forecast', store=False)

    @api.multi
    def create_forecast(self):
        view_id = self.env.ref('project_forecast.project_forecast_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.forecast',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {
                'default_project_id': self.project_id.id,
                'default_task_id': self.id,
                'default_user_id': self.user_id.id,
            }
        }

# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.osv import expression

import odoo.exceptions


class Forecast(models.Model):
    _inherit = "project.forecast"

    def _grid_start_of(self, span, step, anchor):
        if span != 'project':
            return super(Forecast, self)._grid_start_of(span, step, anchor)

        if self.env.context.get('default_project_id'):
            project = self.env['project.project'].browse(self.env.context['default_project_id'])
        elif self.env.context.get('default_task_id'):
            project = self.env['project.task'].browse(self.env.context['default_task_id']).project_id

        if step != 'month':
            raise odoo.exceptions.UserError(
                _("Forecasting over a project only supports monthly forecasts (got step {})").format(step)
            )
        if not project.date_start:
            raise odoo.exceptions.UserError(
                _("A project must have a start date to use a forecast grid, "
                  "found no start date for {project.display_name}").format(
                    project=project
                )
            )
        return fields.Date.from_string(project.date_start).replace(day=1)

    def _grid_end_of(self, span, step, anchor):
        if span != 'project':
            return super(Forecast, self)._grid_end_of(span, step, anchor)

        if self.env.context.get('default_project_id'):
            project = self.env['project.project'].browse(self.env.context['default_project_id'])
        elif self.env.context.get('default_task_id'):
            project = self.env['project.task'].browse(self.env.context['default_task_id']).project_id

        if not project.date:
            raise odoo.exceptions.UserError(
                _("A project must have an end date to use a forecast grid, "
                  "found no end date for {project.display_name}").format(
                    project=project
                )
            )
        return fields.Date.from_string(project.date)

    def _grid_pagination(self, field, span, step, anchor):
        if span != 'project':
            return super(Forecast, self)._grid_pagination(field, span, step, anchor)
        return False, False

    @api.multi
    def adjust_grid(self, row_domain, column_field, column_value, cell_field, change):
        if column_field != 'start_date' or cell_field != 'resource_hours':
            raise odoo.exceptions.UserError(
                _("Grid adjustment for project forecasts only supports the "
                  "'start_date' columns field and the 'resource_hours' cell "
                  "field, got respectively %(column_field)r and "
                  "%(cell_field)r") % {
                    'column_field': column_field,
                    'cell_field': cell_field,
                }
            )

        from_, to_ = map(fields.Date.from_string, column_value.split('/'))
        start = fields.Date.to_string(from_)
        # range is half-open get the actual end date
        end = fields.Date.to_string(to_ - relativedelta(days=1))

        # see if there is an exact match
        cell = self.search(expression.AND([row_domain, [
            '&',
            ['start_date', '=', start],
            ['end_date', '=', end]
        ]]), limit=1)
        # if so, adjust in-place
        if cell:
            cell[cell_field] += change
            return False

        # otherwise copy an existing cell from the row, ignore eventual
        # non-monthly forecast
        # TODO: maybe expand the non-monthly forecast to a fully monthly forecast?
        self.search(row_domain, limit=1).ensure_one().copy({
            'start_date': start,
            'end_date': end,
            cell_field: change,
        })
        return False

    @api.multi
    def project_forecast_assign(self):
        # necessary to forward the default_project_id, otherwise it's
        # stripped out by the context forwarding of actions execution
        [action] = self.env.ref('project_forecast_grid.action_project_forecast_assign').read()

        action['context'] = {
            'default_project_id': self.env.context.get('default_project_id'),
            'default_task_id': self.env.context.get('default_task_id')
        }
        return action

    @api.model
    def _read_forecast_tasks(self, tasks, domain, order):
        tasks_domain = [('id', 'in', tasks.ids)]
        if 'default_project_id' in self.env.context:
            tasks_domain = expression.OR([
                tasks_domain,
                [('project_id', '=', self.env.context['default_project_id'])]
            ])
        return tasks.sudo().search(tasks_domain, order=order)

    task_id = fields.Many2one(group_expand='_read_forecast_tasks')

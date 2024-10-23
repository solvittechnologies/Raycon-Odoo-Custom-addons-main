# -*- coding: utf-8 -*-

from odoo import api, exceptions, models, _


class Project(models.Model):
    _inherit = "project.project"

    @api.multi
    def view_monthly_forecast(self):
        self.env.cr.execute("""
            SELECT count(*)
            FROM project_forecast
            WHERE project_id = %s
              AND date_trunc('month', start_date) != date_trunc('month', end_date);
        """, [self.id])
        [count] = self.env.cr.fetchone()
        if count:
            raise exceptions.UserError(
                _("Can only be used for forecasts not spanning multiple months, "
                  "found %(forecast_count)d forecast(s) spanning across "
                  "months in %(project_name)s") % {
                    'forecast_count': count,
                    'project_name': self.display_name,
                }
            )

        # forecast grid requires start and end dates on the project
        if not (self.date_start and self.date):
            return {
                'name': self.display_name,
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'target': 'new',
                'res_id': self.id,
                'view_mode': 'form',
                'view_id': self.env.ref('project_forecast_grid.view_project_set_dates').id,
            }

        return {
            'name': _("Forecast"),
            'type': 'ir.actions.act_window',
            'res_model': 'project.forecast',
            'view_id': self.env.ref('project_forecast_grid.project_forecast_grid').id,
            'view_mode': 'grid',
            'domain': [['project_id', '=', self.id]],
            'context': {
                'default_project_id': self.id,
            }
        }

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MrpConfigSettings(models.TransientModel):
    _inherit = 'mrp.config.settings'

    manufacturing_period = fields.Selection(related="company_id.manufacturing_period", string="Manufacturing Period")

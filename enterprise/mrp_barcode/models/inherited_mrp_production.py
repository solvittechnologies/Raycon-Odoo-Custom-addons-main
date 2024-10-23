# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpProduction(models.Model):
    _name = 'mrp.production'
    _inherit = ['mrp.production']


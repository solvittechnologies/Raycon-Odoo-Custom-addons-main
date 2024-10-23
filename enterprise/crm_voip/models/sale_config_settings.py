# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleConfigSettings(models.TransientModel):
    _name = 'sale.config.settings'
    _inherit = 'sale.config.settings'

    wsServer = fields.Char("WebSocket", help="The URL of your WebSocket")
    pbx_ip = fields.Char("PBX Server IP", help="The IP adress of your PBX Server")
    mode = fields.Selection([
        ('demo', 'Demo'),
        ('prod', 'Production'),
    ], string="Mode")

    @api.multi
    def set_pbx_ip(self):
        self.env['ir.config_parameter'].set_param('crm.voip.pbx_ip', self[0].pbx_ip, groups=["base.group_system"])

    @api.multi
    def set_wsServer(self):
        self.env['ir.config_parameter'].set_param('crm.voip.wsServer', self[0].wsServer, groups=["base.group_system"])

    @api.multi
    def set_mode(self):
        self.env['ir.config_parameter'].set_param('crm.voip.mode', self[0].mode, groups=["base.group_system"])

    @api.model
    def get_default_pbx_ip(self, fields):
        params = self.env['ir.config_parameter']
        pbx_ip = params.get_param('crm.voip.pbx_ip', default='localhost')
        return {'pbx_ip': pbx_ip}

    @api.model
    def get_default_wsServer(self, fields):
        params = self.env['ir.config_parameter']
        wsServer = params.get_param('crm.voip.wsServer', default='ws://localhost')
        return {'wsServer': wsServer}

    @api.model
    def get_default_mode(self, fields):
        params = self.env['ir.config_parameter']
        mode = params.get_param('crm.voip.mode', default="demo")
        return {'mode': mode}

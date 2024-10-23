# -*- coding: utf-8 -*-

from odoo import models, fields


class User(models.Model):
    _inherit = 'res.users'

    # TDE FIXME: this does not seem necessary to me, probably to remove
    resource_ids = fields.One2many('resource.resource', 'user_id')

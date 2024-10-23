# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

# add sip_password to the fields that only users who can modify the user (incl. the user herself) see their real contents
from odoo.addons.base.res import res_users
res_users.USER_PRIVATE_FIELDS.append('sip_password')

class ResUsers(models.Model):
    _inherit = 'res.users'

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
            Access rights are disabled by default, but allowed
            on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(ResUsers, self).__init__(pool, cr)
        voip_fields = [
            'sip_login',
            'sip_password',
            'sip_external_phone',
            'sip_always_transfer',
            'sip_ring_number'
        ]
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(voip_fields)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(voip_fields)
        return init_res

    sip_login = fields.Char("SIP Login / Browser's Extension", groups="base.group_user")
    sip_password = fields.Char('SIP Password', groups="base.group_user")
    sip_external_phone = fields.Char("Handset Extension", groups="base.group_user")
    sip_always_transfer = fields.Boolean("Always Redirect to Handset", default=False,
                                         groups="base.group_user")
    sip_ring_number = fields.Integer(
        "Number of rings", default=6,
        help="The number of rings before the call is defined as refused by the customer.",
        groups="base.group_user")

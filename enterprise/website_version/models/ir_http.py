# -*- coding: utf-8 -*-

from odoo.http import request
from odoo.osv import orm
import json

class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):
        x = super(ir_http, cls)._dispatch()
        if request.context.get('website_version_experiment'):
            data=json.dumps(request.context['website_version_experiment'], ensure_ascii=False)
            x.set_cookie('website_version_experiment', data)
        return x

    @classmethod
    def get_page_key(cls):
        key = super(ir_http, cls).get_page_key()
        if hasattr(request, 'website'):
            key += (request.website.id,)
        seq_ver = [int(ver) for ver in request.context.get('website_version_experiment', {}).values()]
        key += (str(sorted(seq_ver)),)
        return key

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import unicodedata
import uuid
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr


def sanitize_for_xmlid(s):
    """ Transforms a string to a name suitable for use in an xmlid.
        Strips leading and trailing spaces, converts unicode chars to ascii,
        lowers all chars, replaces spaces with underscores and truncates the
        resulting string to 20 characters.
        :param s: str
        :rtype: str
    """
    s = ustr(s)
    uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

    slug_str = re.sub('[\W]', ' ', uni).strip().lower()
    slug_str = re.sub('[-\s]+', '_', slug_str)
    return slug_str[:20]


class Base(models.AbstractModel):
    _inherit = 'base'

    def create_studio_model_data(self, name):
        """ We want to keep track of created records with studio
            (ex: model, field, view, action, menu, etc.).
            An ir.model.data is created whenever a record of one of these models
            is created, tagged with studio.
        """
        IrModelData = self.env['ir.model.data']

        # Check if there is already an ir.model.data for the given resource
        data = IrModelData.search([
            ('model', '=', self._name), ('res_id', '=', self.id)
        ])
        if data:
            data.write({})  # force a write to set the 'studio' and 'noupdate' flags to True
        else:
            module = self.env['ir.module.module'].get_studio_module()
            IrModelData.create({
                'name': '%s_%s' % (sanitize_for_xmlid(name), uuid.uuid4()),
                'model': self._name,
                'res_id': self.id,
                'module': module.name,
            })


class IrModel(models.Model):
    _name = 'ir.model'
    _inherit = ['studio.mixin', 'ir.model']

    mail_thread = fields.Boolean(compute='_compute_mail_thread',
                                 inverse='_inverse_mail_thread', store=True,
                                 help="Whether this model supports messages and notifications.")

    abstract = fields.Boolean(compute='_compute_abstract',
                              store=False,
                              help="Wheter this model is abstract",
                              search='_search_abstract')

    @api.depends('model')
    def _compute_mail_thread(self):
        MailThread = self.pool['mail.thread']
        for rec in self:
            if rec.model != 'mail.thread':
                Model = self.pool.get(rec.model)
                rec.mail_thread = Model and issubclass(Model, MailThread)

    def _inverse_mail_thread(self):
        pass        # do nothing; this enables to set the value of the field

    def _compute_abstract(self):
        for record in self:
            record.abstract = self.env[record.model]._abstract

    def _search_abstract(self, operator, value):
        abstract_models = [
            model._name
            for model in self.env.itervalues()
            if model._abstract
        ]
        dom_operator = 'in' if (operator, value) in [('=', True), ('!=', False)] else 'not in'

        return [('model', dom_operator, abstract_models)]

    @api.model
    def create(self, vals):
        res = super(IrModel, self).create(vals)

        # Create a simplified form view and access rights for the created model
        # if we are in studio, but not if we are currently installing the module
        # (i.e. importing it from Studio), because those data are already
        # defined in the module (as Studio generates them automatically)
        if self._context.get('studio') and not self._context.get('install_mode'):
            # Create a simplified form view to prevent getting the default one containing all model's fields
            self.env['ir.ui.view'].create_simplified_form_view(res.model)

            # Give read access to the created model to Employees by default and all access to System
            # Note: a better solution may be to create groups at the app creation but the model is created
            # before the app and for other models we need to have info about the app.
            self.env['ir.model.access'].create({
                'name': vals.get('name', '') + ' group_system',
                'model_id': res.id,
                'group_id': self.env.ref('base.group_system').id,
                'perm_read': True,
                'perm_write': True,
                'perm_create': True,
                'perm_unlink': True,
            })
            self.env['ir.model.access'].create({
                'name': vals.get('name', '') + ' group_user',
                'model_id': res.id,
                'group_id': self.env.ref('base.group_user').id,
                'perm_read': True,
                'perm_write': False,
                'perm_create': False,
                'perm_unlink': False,
            })
        return res

    @api.multi
    def write(self, vals):
        res = super(IrModel, self).write(vals)
        if self and 'mail_thread' in vals:
            if not all(rec.state == 'manual' for rec in self):
                raise UserError(_('Only custom models can be modified.'))
            # one can only change mail_thread from False to True
            if not all(rec.mail_thread <= vals['mail_thread'] for rec in self):
                raise UserError(_('Field "Mail Thread" cannot be changed to "False".'))
            # setup models; this reloads custom models in registry
            self.pool.setup_models(self._cr, partial=(not self.pool.ready))
            # update database schema of models
            models = self.pool.descendants(self.mapped('model'), '_inherits')
            self.pool.init_models(self._cr, models, dict(self._context, update_custom_fields=True))
            self.pool.signal_registry_change()
        return res

    @api.model
    def _instanciate(self, model_data):
        model_class = super(IrModel, self)._instanciate(model_data)
        if model_data.get('mail_thread'):
            parents = model_class._inherit or []
            parents = [parents] if isinstance(parents, basestring) else parents
            model_class._inherit = parents + ['mail.thread']
        return model_class


class IrModelField(models.Model):
    _name = 'ir.model.fields'
    _inherit = ['studio.mixin', 'ir.model.fields']

    track_visibility = fields.Selection(
        [('onchange', "On Change"), ('always', "Always")], string="Tracking",
        compute='_compute_track_visibility', inverse='_inverse_track_visibility', store=True,
        help="When set, every modification to this field will be tracked in the chatter.",
    )

    @api.depends('name')
    def _compute_track_visibility(self):
        for rec in self:
            if rec.model in self.env:
                field = self.env[rec.model]._fields.get(rec.name)
                rec.track_visibility = getattr(field, 'track_visibility', False)

    def _inverse_track_visibility(self):
        pass        # do nothing; this enables to set the value of the field

    @api.model
    def _instanciate(self, field_data, partial):
        field = super(IrModelField, self)._instanciate(field_data, partial)
        if field and field_data.get('track_visibility'):
            field.args = dict(field.args, track_visibility=field_data['track_visibility'])
        return field


class IrModelAccess(models.Model):
    _name = 'ir.model.access'
    _inherit = ['studio.mixin', 'ir.model.access']

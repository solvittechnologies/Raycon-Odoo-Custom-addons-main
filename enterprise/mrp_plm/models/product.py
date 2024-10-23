# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ProductProduct(models.Model):
    _inherit = 'product.product'
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'product.product')], string='Attachments')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    eco_inprogress = fields.Boolean('ECO in progress?', compute='_compute_eco_data')
    eco_inprogress_count = fields.Integer('# ECOs in progress', compute='_compute_eco_data', groups="mrp_plm.group_plm_user")
    attachment_count = fields.Integer('# Attachments', compute='_compute_attachments')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'product.template')], string='Attachments')

    @api.multi
    def _compute_eco_data(self):
        eco_data = self.env['mrp.eco'].read_group([
            ('product_tmpl_id', 'in', self.ids),
            ('state', '=', 'progress')],
            ['product_tmpl_id'], ['product_tmpl_id'])
        result = dict((data['product_tmpl_id'][0], data['product_tmpl_id_count']) for data in eco_data)
        for eco in self:
            eco.eco_inprogress_count = result.get(eco.id, 0)
            eco.eco_inprogress = bool(eco.eco_inprogress_count)

    @api.multi
    def _compute_attachments(self):
        for p in self:
            count = len(p.attachment_ids)
            for v in p.product_variant_ids:
                count += len(v.attachment_ids)
            p.attachment_count = count

    @api.multi
    def action_see_attachments(self):
        domain = [
            '|',
            '&', ('res_model', '=', 'product.product'), ('res_id', 'in', self.product_variant_ids.mapped('id')),
            '&', ('res_model', '=', 'product.template'), ('res_id', '=', self.id)]
        attachment_view = self.env.ref('mrp.view_document_file_kanban_mrp')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Click to upload files to your product.
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.template', self.id)
        }


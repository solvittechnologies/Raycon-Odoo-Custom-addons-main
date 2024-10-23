# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    version = fields.Integer('Version', default=0)
    previous_bom_id = fields.Many2one('mrp.bom', 'Previous BoM')
    active = fields.Boolean('Production Ready')
    image_small = fields.Binary(related='product_tmpl_id.image_small')
    eco_ids = fields.One2many(
        'mrp.eco', 'new_bom_id', 'ECO to be applied')
    eco_count = fields.Integer('# ECOs', compute='_compute_eco_data')
    eco_inprogress_count = fields.Integer("# ECOs in progress", compute='_compute_eco_data')
    revision_ids = fields.Many2many('mrp.bom', compute='_compute_revision_ids')

    @api.multi
    def _compute_eco_data(self):
        eco_data = self.env['mrp.eco'].read_group([
            ('product_tmpl_id', 'in', self.mapped('product_tmpl_id').ids),
            ('state', '=', 'progress')],
            ['product_tmpl_id'], ['product_tmpl_id'])
        result = dict((data['product_tmpl_id'][0], data['product_tmpl_id_count']) for data in eco_data)
        for bom in self:
            bom.eco_count = len(bom.eco_ids)
            bom.eco_inprogress_count = result.get(bom.product_tmpl_id.id, 0)

    @api.one
    def _compute_revision_ids(self):
        previous_boms = self.env['mrp.bom']
        current = self
        while current.previous_bom_id:
            previous_boms |= current
            current = current.previous_bom_id
        self.revision_ids = previous_boms.ids

    @api.multi
    def apply_new_version(self):
        """ Put old BoM as deprecated - TODO: Set to stage that is production_ready """
        self.write({'active': True})
        self.mapped('previous_bom_id').write({'active': False})

    @api.multi
    def button_mrp_eco(self):
        self.ensure_one()
        action = self.env.ref('mrp_plm.mrp_eco_action_main').read()[0]
        action['domain'] = [('id', 'in', self.eco_ids.ids)]
        action['context'] = {
            'default_bom_id': self.id,
            'default_product_tmpl_id': self.product_tmpl_id.id
        }
        return action

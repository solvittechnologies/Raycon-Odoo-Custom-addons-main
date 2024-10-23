# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _

class MrpWorkorder(models.Model):
    _name = 'mrp.workorder'
    _inherit = ['mrp.workorder', 'barcodes.barcode_events_mixin']

    def on_barcode_scanned(self, barcode):
        self.ensure_one()
        barcode_nomenclature = self.production_id.picking_type_id.barcode_nomenclature_id
        if not barcode_nomenclature:
            if self.product_id.barcode == barcode:
                if self.qty_producing < self.qty_production:
                    self.qty_producing += 1
                else:
                    self.qty_producing = 1
            elif self.active_move_lot_ids or self.product_id.tracking != 'none':
                lot = self.env['stock.production.lot'].search([('name', '=', barcode)], limit=1)
                if lot.product_id == self.product_id:
                    self.final_lot_id = lot
                else:
                    active_move_lots = self.active_move_lot_ids.filtered(lambda l: l.product_id == lot.product_id)
                    if active_move_lots:
                        blank_move_lot = active_move_lots.filtered(lambda m: not m.lot_id)
                        move_lots = active_move_lots.filtered(lambda m: m.lot_id.name == barcode)
                        if move_lots:
                            move_lots[0].quantity_done += 1.0 # Problem is it will immediately consume more than foreseen on the second scan (check if it becomes red)
                        elif blank_move_lot:
                            blank_move_lot[0].lot_id = lot.id
                        else:
                            self.active_move_lot_ids.new({'move_id': active_move_lots[0].move_id, 
                                                          'lot_id': lot.id,
                                                          'quantity_done': 1.0,
                                                          'quantity': 0.0,
                                                          'workorder_id': self.id,
                                                          'production_id': self.production_id.id,
                                                          'product_id': lot.product_id.id,
                                                          'done_wo': False})
        else:
            parsed_result = self.picking_type_id.barcode_nomenclature_id.parse_barcode(barcode)
            if parsed_result['type'] in ['weight', 'product']:
                if parsed_result['type'] == 'weight':
                    product_barcode = parsed_result['base_code']
                    qty = parsed_result['value']
                else: #product
                    product_barcode = parsed_result['code']
                    qty = 1.0
                if self.product_id.barcode == product_barcode:
                    if self.qty_producing + qty <= self.qty_production:
                        self.qty_producing += qty
                    else:
                        self.qty_producing = qty
            elif parsed_result['type'] == 'lot':
                lot = self.env['stock.production.lot'].search([('name', '=', parsed_result["code"])], limit=1)
                if lot:
                    if lot.product_id == self.product_id:
                        self.final_lot_id = lot
                    else:
                        active_move_lots = self.active_move_lot_ids.filtered(lambda l: l.product_id == parsed_result['code'])
                        if active_move_lots:
                            blank_move_lot = active_move_lots.filtered(lambda m: not m.lot_id)
                            move_lots = active_move_lots.filtered(lambda m: m.lot_id.name == barcode)
                            if move_lots:
                                move_lots[0].quantity_done += 1.0 # Problem is it will immediately consume more than foreseen on the second scan (check if it becomes red)
                            elif blank_move_lot:
                                blank_move_lot[0].lot_id = lot.id
                            else:
                                self.active_move_lot_ids.new({'move_id': active_move_lots[0].move_id, 
                                                          'lot_id': lot.id,
                                                          'quantity_done': 1.0,
                                                          'quantity': 0.0,
                                                          'workorder_id': self.id,
                                                          'production_id': self.production_id.id,
                                                          'product_id': lot.product_id.id,
                                                          'done_wo': False})
                elif not self.final_lot_id:
                    self.final_lot_id = self.env['stock.production.lot'].create({'product_id': self.product_id.id,
                                                                                 'name': parsed_result['code']})
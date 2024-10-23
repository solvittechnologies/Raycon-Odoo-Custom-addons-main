# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tests import common


class TestMrpAccount(common.TransactionCase):

    def setUp(self):
        super(TestMrpAccount, self).setUp()
        self.categ_standard = self.env['product.category'].create({'name': 'STANDARD',
                                                              'property_cost_method': 'standard',},)
        self.categ_real = self.env['product.category'].create({'name': 'REAL',
                                                          'property_cost_method': 'real',})
        self.categ_average = self.env['product.category'].create({'name': 'AVERAGE',
                                                             'property_cost_method': 'average'})
        self.dining_table = self.env.ref("mrp.product_product_computer_desk")
        self.dining_table.categ_id = self.categ_real.id
        self.product_table_sheet = self.env.ref('mrp.product_product_computer_desk_head')
        self.product_table_sheet.categ_id = self.categ_real.id
        self.product_table_leg = self.env.ref('mrp.product_product_computer_desk_leg')
        self.product_table_leg.categ_id = self.categ_average.id
        self.product_bolt = self.env.ref('mrp.product_product_computer_desk_bolt')
        self.product_bolt.categ_id = self.categ_standard.id
        self.source_location_id = self.ref('stock.stock_location_14')
    
    def test_00_production_order_with_accounting(self):
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory Product Table',
            'filter': 'partial',
            'line_ids': [(0, 0, {
                'product_id': self.product_table_sheet.id,
                'product_uom_id': self.product_table_sheet.uom_id.id,
                'product_qty': 20,
                'location_id': self.source_location_id
            }), (0, 0, {
                'product_id': self.product_table_leg.id,
                'product_uom_id': self.product_table_leg.uom_id.id,
                'product_qty': 20,
                'location_id': self.source_location_id
            }), (0, 0, {
                'product_id': self.product_bolt.id,
                'product_uom_id': self.product_bolt.uom_id.id,
                'product_qty': 20,
                'location_id': self.source_location_id
            })]
        })
        inventory.action_done()
        # Write costs on quants like they would come from a purchase
        # As we don't have the purchase module installed with this one
        self.product_table_sheet.standard_price = 10.0
        quants = inventory.move_ids.filtered(lambda x: x.product_id == self.product_table_sheet).mapped('quant_ids')
        quants.write({'cost': 20.0})
        
        self.product_table_leg.standard_price = 15.0
        quants = inventory.move_ids.filtered(lambda x: x.product_id == self.product_table_leg).mapped('quant_ids')
        quants.write({'cost': 30.0})
        
        self.product_bolt.standard_price = 10.0
        quants = inventory.move_ids.filtered(lambda x: x.product_id == self.product_bolt).mapped('quant_ids')
        quants.write({'cost': 30.0})
        
        self.env.ref('mrp.mrp_bom_desk').routing_id = False # TODO: extend the test later with the necessary operations
        production_table = self.env['mrp.production'].create({
            'product_id': self.dining_table.id,
            'product_qty': 5.0,
            'product_uom_id': self.dining_table.uom_id.id,
            'bom_id': self.ref("mrp.mrp_bom_desk")
        })
        
        produce_wizard = self.env['mrp.product.produce'].with_context({
            'active_id': production_table.id,
            'active_ids': [production_table.id],
        }).create({
            'product_qty': 1.0,
        })
        produce_wizard.do_produce()
        production_table.post_inventory()
        quant_value = production_table.move_finished_ids.filtered(lambda x: x.state == "done").quant_ids[0].inventory_value
        
        # Real price of the head (quant: 20) + avg price leg (product: 4*15) + standard price bolt (product: 4*10)
        self.assertEqual(quant_value, 120, 'Thing should have the correct price')
        
        produce_wizard = self.env['mrp.product.produce'].with_context({
            'active_id': production_table.id,
            'active_ids': [production_table.id],
        }).create({
            'product_qty': 2.0,
        })
        produce_wizard.do_produce()
        production_table.post_inventory()
        quant_value = production_table.move_finished_ids.filtered(lambda x: x.state == "done" and x.product_qty == 2.0).quant_ids[0].inventory_value
        # 2 * Real price of the head (quant: 20) + avg price leg (product: 4*15) + standard price bolt (product: 4*10)
        self.assertEqual(quant_value, 240, 'Thing should have the correct price')
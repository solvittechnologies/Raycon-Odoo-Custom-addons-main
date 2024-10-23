# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import unittest
from odoo.tests.common import TransactionCase


class TestDeliveryUPS(TransactionCase):

    def setUp(self):
        super(TestDeliveryUPS, self).setUp()

        self.iPadMini = self.env.ref('product.product_product_6')
        self.iMac = self.env.ref('product.product_product_8')
        self.uom_unit = self.env.ref('product.product_uom_unit')

        # Add a full address to "Your Company" and "Agrolait"
        self.your_company = self.env.ref('base.main_partner')
        self.your_company.write({'country_id': self.env.ref('base.us').id,
                                 'state_id': self.env.ref('base.state_us_5').id,
                                 'city': 'San Francisco',
                                 'street': '51 Federal Street',
                                 'zip': '94107'})
        self.agrolait = self.env.ref('base.res_partner_2')
        self.agrolait.write({'country_id': self.env.ref('base.be').id,
                             'city': 'Auderghem-Ouderghem',
                             'street': 'Avenue Edmond Van Nieuwenhuyse',
                             'zip': '1160'})

    @unittest.skip("UPS test disabled: We do not want to overload UPS with runbot's requests")
    def test_01_ups_basic_flow(self):
        SaleOrder = self.env['sale.order']

        sol_vals = {'product_id': self.iPadMini.id,
                    'name': "[A1232] iPad Mini",
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                    'price_unit': self.iPadMini.lst_price}

        # Set service type = 'UPS Worldwide Expedited', which is available between US to BE
        carrier = self.env.ref('delivery_ups.delivery_carrier_ups_us')
        carrier.write({'ups_default_service_type': '08',
                       'ups_package_dimension_unit': 'IN'})
        carrier.ups_default_packaging_id.write({
                       'height': '3',
                       'width': '3',
                       'length': '3'})

        so_vals = {'partner_id': self.agrolait.id,
                   'carrier_id': carrier.id,
                   'order_line': [(0, None, sol_vals)]}

        sale_order = SaleOrder.create(so_vals)
        self.assertGreater(sale_order.delivery_price, 0.0, "UPS delivery cost for this SO has not been correctly estimated.")

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.force_assign()

        self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")

        picking.pack_operation_product_ids.qty_done = 1.0
        picking.do_transfer()

        self.assertIsNot(picking.carrier_tracking_ref, False, "UPS did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "UPS carrying price is probably incorrect")

        picking.cancel_shipment()

        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

    @unittest.skip("UPS test disabled: We do not want to overload UPS with runbot's requests")
    def test_02_ups_multipackage_flow(self):
        SaleOrder = self.env['sale.order']

        # Set packaging type = 'Pallet' and service type = 'UPS Worldwide Express Freight'
        # so in this case height, width and length required.
        carrier = self.env.ref('delivery_ups.delivery_carrier_ups_us')
        carrier.write({'ups_default_packaging_id': self.env.ref('delivery_ups.ups_packaging_30').id,
                       'ups_default_service_type': '96',
                       'ups_package_dimension_unit': 'IN'})
        carrier.ups_default_packaging_id.write({
                       'height': '3',
                       'width': '3',
                       'length': '3'})

        sol_1_vals = {'product_id': self.iPadMini.id,
                      'name': "[A1232] iPad Mini",
                      'product_uom': self.uom_unit.id,
                      'product_uom_qty': 1.0,
                      'price_unit': self.iPadMini.lst_price}

        sol_2_vals = {'product_id': self.iMac.id,
                      'name': "[A1090] iMac",
                      'product_uom': self.uom_unit.id,
                      'product_uom_qty': 1.0,
                      'price_unit': self.iMac.lst_price}

        so_vals = {'partner_id': self.agrolait.id,
                   'carrier_id': carrier.id,
                   'order_line': [(0, None, sol_1_vals), (0, None, sol_2_vals)]}

        sale_order = SaleOrder.create(so_vals)
        self.assertGreater(sale_order.delivery_price, 0.0, "UPS delivery cost for this SO has not been correctly estimated.")

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.force_assign()

        # We put pack each product separately
        po0 = picking.pack_operation_product_ids[0]
        po1 = picking.pack_operation_product_ids[1]
        po0.qty_done = 1
        picking.put_in_pack()
        po1.qty_done = 1
        picking.put_in_pack()

        self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")
        self.assertTrue(all([po.result_package_id is not False for po in picking.pack_operation_product_ids]), "Some products have not been put in packages")

        picking.do_transfer()

        self.assertIsNot(picking.carrier_tracking_ref, False, "UPS did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "UPS carrying price is probably incorrect")

        picking.cancel_shipment()

        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

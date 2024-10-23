# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import unittest
from odoo.tests.common import TransactionCase


class TestDeliveryTemando(TransactionCase):

    def setUp(self):
        super(TestDeliveryTemando, self).setUp()

        self.iPadMini = self.env.ref('product.product_product_6')
        self.iMac = self.env.ref('product.product_product_8')
        self.uom_unit = self.env.ref('product.product_uom_unit')

        self.aud = self.env.ref('base.AUD')
        self.pricelist = self.env.ref('product.list0')

        self.your_company = self.env.ref('base.main_partner')
        self.your_company.write({'street': 'Test Street',
                                 'zip': 2000,
                                 'state_id': self.env.ref('base.state_au_2').id,
                                 'city': 'Sydney',
                                 'country_id': self.env.ref('base.au').id,
                                 'phone': 9874582356,
                                 'email': 'shipper@example.com'})
        Partner = self.env['res.partner']
        self.test_company_au = Partner.create({'name': 'Test Company',
                                               'street': 'Test Street',
                                               'zip': 5097,
                                               'state_id': self.env.ref('base.state_au_5').id,
                                               'city': 'Ridgehaven',
                                               'country_id': self.env.ref('base.au').id,
                                               'phone': 1234567891,
                                               'email': 'test@company.au.example.com'})
        self.odoo_usa = Partner.create({'name': 'Odoo Inc.',
                                                'street': '44 Federal Street',
                                                'zip': 94107,
                                                'state_id': self.env.ref('base.state_us_5').id,
                                                'city': 'San Francisco',
                                                'country_id': self.env.ref('base.us').id,
                                                'phone': 1234567891,
                                                'email': 'odoo@usa.example.com'})

    @unittest.skip("Temando test disabled: We do not want to overload Temando with runbot's requests")
    def test_01_temando_basic_au_domestic_flow(self):
        SaleOrder = self.env['sale.order']

        sol_vals = {'product_id': self.iPadMini.id,
                    'name': "[A1232] iPad Mini",
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                    'price_unit': self.iPadMini.lst_price}
        self.pricelist.currency_id = self.aud.id
        so_vals = {'partner_id': self.test_company_au.id,
                   'carrier_id': self.env.ref('delivery_temando.delivery_carrier_temando').id,
                   'order_line': [(0, None, sol_vals)]}
        sale_order = SaleOrder.create(so_vals)

        self.assertGreater(sale_order.delivery_price, 0.0, "temando delivery cost for this SO has not been correctly estimated.")

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.force_assign()

        picking.pack_operation_product_ids.qty_done = 1.0

        self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")

        picking.do_transfer()

        self.assertIsNot(picking.carrier_tracking_ref, False, "Temando did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "Temando carrying price is probably incorrect")

        picking.cancel_shipment()

        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

    @unittest.skip("Temando test disabled: We do not want to overload Temando with runbot's requests")
    def test_02_temando_multipackage_au_flow(self):
        SaleOrder = self.env['sale.order']

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
        self.pricelist.currency_id = self.aud.id
        so_vals = {'partner_id': self.test_company_au.id,
                   'carrier_id': self.env.ref('delivery_temando.delivery_carrier_temando').id,
                   'order_line': [(0, None, sol_1_vals), (0, None, sol_2_vals)]}
        sale_order = SaleOrder.create(so_vals)

        self.assertGreater(sale_order.delivery_price, 0.0, "Temando delivery cost for this SO has not been correctly estimated.")

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.force_assign()

        po0 = picking.pack_operation_product_ids[0]
        po1 = picking.pack_operation_product_ids[1]
        po0.qty_done = 1
        picking.put_in_pack()
        po1.qty_done = 1
        picking.put_in_pack()

        self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")
        self.assertTrue(all([po.result_package_id is not False for po in picking.pack_operation_ids]), "Some products have not been put in packages")

        picking.do_transfer()

        self.assertIsNot(picking.carrier_tracking_ref, False, "Temando did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "Temando carrying price is probably incorrect")

        picking.cancel_shipment()

        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

    @unittest.skip("Temando test disabled: We do not want to overload Temando with runbot's requests")
    def test_03_temando_basic_international_flow(self):
        # Force use of TNT Australia for international shipping
        tnt_international_australia = self.env.ref('delivery_temando.temando_60412')
        tnt_international_australia.write({'active': True,
                                           'temando_username': 'TEMANDOTEST',
                                           'temando_password': 'temandopass1',
                                           'temando_client_id': 20420,
                                           'temando_delivery_nature': 'International',
                                           'temando_hs_code': '123456789012'})

        SaleOrder = self.env['sale.order']

        sol_vals = {'product_id': self.iPadMini.id,
                    'name': "[A1232] iPad Mini",
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                    'price_unit': self.iPadMini.lst_price}
        self.pricelist.currency_id = self.aud.id
        so_vals = {'partner_id': self.odoo_usa.id,
                   'carrier_id': tnt_international_australia.id,
                   'order_line': [(0, None, sol_vals)]}
        sale_order = SaleOrder.create(so_vals)

        self.assertGreater(sale_order.delivery_price, 0.0, "temando delivery cost for this SO has not been correctly estimated.")

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.force_assign()

        picking.pack_operation_product_ids.qty_done = 1.0

        self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")

        picking.do_transfer()

        self.assertIsNot(picking.carrier_tracking_ref, False, "Temando did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "Temando carrying price is probably incorrect")

        picking.cancel_shipment()

        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

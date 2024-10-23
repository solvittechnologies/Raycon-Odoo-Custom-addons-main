# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import unittest
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


# These errors are due to failures of Fedex test server and are not implementation errors
ERROR_200 = u"200: Rating is temporarily unavailable, please try again later."
ERROR_200_BIS = u"200: An unexpected exception occurred"
ERROR_200_TER = u"200: An unexpected exception occurred, not found"
ERROR_1000 = u"1000: General Failure"
SKIPPABLE_ERRORS = [ERROR_200, ERROR_200_BIS, ERROR_200_TER, ERROR_1000]
SKIP_MSG = u"Test skipped due to FedEx server unavailability"


class TestDeliveryFedex(TransactionCase):

    def setUp(self):
        super(TestDeliveryFedex, self).setUp()

        self.iPadMini = self.env.ref('product.product_product_6')
        self.iMac = self.env.ref('product.product_product_8')
        self.uom_unit = self.env.ref('product.product_uom_unit')

        self.your_company = self.env.ref('base.main_partner')
        self.agrolait = self.env.ref('base.res_partner_2')
        self.agrolait.write({'country_id': self.env.ref('base.be').id})
        self.delta_pc = self.env.ref('base.res_partner_4')

    @unittest.skip("Fedex test disabled: We do not want to overload Fedex with runbot's requests")
    def test_01_fedex_basic_us_domestic_flow(self):
        try:

            SaleOrder = self.env['sale.order']

            sol_vals = {'product_id': self.iPadMini.id,
                        'name': "[A1232] iPad Mini",
                        'product_uom': self.uom_unit.id,
                        'product_uom_qty': 1.0,
                        'price_unit': self.iPadMini.lst_price}

            so_vals = {'partner_id': self.delta_pc.id,
                       'carrier_id': self.env.ref('delivery_fedex.delivery_carrier_fedex_us').id,
                       'order_line': [(0, None, sol_vals)]}

            sale_order = SaleOrder.create(so_vals)

            self.assertGreater(sale_order.delivery_price, 0.0, "FedEx delivery cost for this SO has not been correctly estimated.")

            sale_order.action_confirm()
            self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

            picking = sale_order.picking_ids[0]
            self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

            picking.force_assign()

            self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")

            picking.pack_operation_product_ids.qty_done = 1.0
            picking.do_transfer()

            self.assertIsNot(picking.carrier_tracking_ref, False, "FedEx did not return any tracking number")
            self.assertGreater(picking.carrier_price, 0.0, "FedEx carrying price is probably incorrect")

            picking.cancel_shipment()

            self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
            self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

        except ValidationError as e:
            if e.name.strip() in SKIPPABLE_ERRORS:
                raise unittest.SkipTest(SKIP_MSG)
            else:
                raise e

    @unittest.skip("Fedex test disabled: We do not want to overload Fedex with runbot's requests")
    def test_02_fedex_basic_international_flow(self):
        try:

            SaleOrder = self.env['sale.order']

            sol_vals = {'product_id': self.iPadMini.id,
                        'name': "[A1232] iPad Mini",
                        'product_uom': self.uom_unit.id,
                        'product_uom_qty': 1.0,
                        'price_unit': self.iPadMini.lst_price}

            so_vals = {'partner_id': self.agrolait.id,
                       'carrier_id': self.env.ref('delivery_fedex.delivery_carrier_fedex_inter').id,
                       'order_line': [(0, None, sol_vals)]}

            sale_order = SaleOrder.create(so_vals)
            self.assertGreater(sale_order.delivery_price, 0.0, "FedEx delivery cost for this SO has not been correctly estimated.")

            sale_order.action_confirm()
            self.assertEquals(len(sale_order.picking_ids), 1, "The Sale Order did not generate a picking.")

            picking = sale_order.picking_ids[0]
            self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

            picking.force_assign()
            self.assertGreater(picking.weight, 0.0, "Picking weight should be positive.")

            picking.pack_operation_product_ids.qty_done = 1.0
            picking.do_transfer()

            self.assertIsNot(picking.carrier_tracking_ref, False, "FedEx did not return any tracking number")
            self.assertGreater(picking.carrier_price, 0.0, "FedEx carrying price is probably incorrect")

            picking.cancel_shipment()

            self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
            self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

        except ValidationError as e:
            if e.name.strip() in SKIPPABLE_ERRORS:
                raise unittest.SkipTest(SKIP_MSG)
            else:
                raise e

    @unittest.skip("Fedex test disabled: We do not want to overload Fedex with runbot's requests")
    def test_03_fedex_multipackage_international_flow(self):
        try:

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

            so_vals = {'partner_id': self.agrolait.id,
                       'carrier_id': self.env.ref('delivery_fedex.delivery_carrier_fedex_inter').id,
                       'order_line': [(0, None, sol_1_vals), (0, None, sol_2_vals)]}

            sale_order = SaleOrder.create(so_vals)
            self.assertGreater(sale_order.delivery_price, 0.0, "FedEx delivery cost for this SO has not been correctly estimated.")

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

            self.assertIsNot(picking.carrier_tracking_ref, False, "FedEx did not return any tracking number")
            self.assertGreater(picking.carrier_price, 0.0, "FedEx carrying price is probably incorrect")

            picking.cancel_shipment()

            self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
            self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

        except ValidationError as e:
            if e.name.strip() in SKIPPABLE_ERRORS:
                raise unittest.SkipTest(SKIP_MSG)
            else:
                raise e

    # TODO RIM master: other tests scenarios:
    # - incomplete addresses:
    #   * no country
    #   * no state in US
    #   * accents in address
    # - no weight for rating
    # - no service availability between 2 addresses
    # - incorrect weight
    # - cancel twice or with incorrect tracking

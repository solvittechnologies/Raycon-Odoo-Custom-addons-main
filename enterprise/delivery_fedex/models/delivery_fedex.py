# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, _
from odoo.exceptions import ValidationError

from fedex_request import FedexRequest


_logger = logging.getLogger(__name__)

# Why using standardized ISO codes? It's way more fun to use made up codes...
# https://www.fedex.com/us/developer/WebHelp/ws/2014/dvg/WS_DVG_WebHelp/Appendix_F_Currency_Codes.htm
FEDEX_CURR_MATCH = {
    u'UYU': u'UYP',
    u'XCD': u'ECD',
    u'MXN': u'NMP',
    u'KYD': u'CID',
    u'CHF': u'SFR',
    u'GBP': u'UKL',
    u'IDR': u'RPA',
    u'DOP': u'RDD',
    u'JPY': u'JYE',
    u'KRW': u'WON',
    u'SGD': u'SID',
    u'CLP': u'CHP',
    u'JMD': u'JAD',
    u'KWD': u'KUD',
    u'AED': u'DHS',
    u'TWD': u'NTD',
    u'ARS': u'ARN',
    u'LVL': u'EURO',
}


class ProviderFedex(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('fedex', "FedEx")])

    fedex_developer_key = fields.Char(string="Developer Key", groups="base.group_system")
    fedex_developer_password = fields.Char(string="Password", groups="base.group_system")
    fedex_account_number = fields.Char(string="Account Number", groups="base.group_system")
    fedex_meter_number = fields.Char(string="Meter Number", groups="base.group_system")
    fedex_droppoff_type = fields.Selection([('BUSINESS_SERVICE_CENTER', 'BUSINESS_SERVICE_CENTER'),
                                            ('DROP_BOX', 'DROP_BOX'),
                                            ('REGULAR_PICKUP', 'REGULAR_PICKUP'),
                                            ('REQUEST_COURIER', 'REQUEST_COURIER'),
                                            ('STATION', 'STATION')],
                                           string="Fedex drop-off type",
                                           default='REGULAR_PICKUP')
    fedex_default_packaging_id = fields.Many2one('product.packaging', string="Default Package Type")
    fedex_service_type = fields.Selection([('INTERNATIONAL_ECONOMY', 'INTERNATIONAL_ECONOMY'),
                                           ('INTERNATIONAL_PRIORITY', 'INTERNATIONAL_PRIORITY'),
                                           ('FEDEX_GROUND', 'FEDEX_GROUND'),
                                           ('FEDEX_2_DAY', 'FEDEX_2_DAY'),
                                           ('FEDEX_2_DAY_AM', 'FEDEX_2_DAY_AM'),
                                           ('FIRST_OVERNIGHT', 'FIRST_OVERNIGHT'),
                                           ('PRIORITY_OVERNIGHT', 'PRIORITY_OVERNIGHT'),
                                           ('STANDARD_OVERNIGHT', 'STANDARD_OVERNIGHT')],
                                          default='INTERNATIONAL_PRIORITY')
    fedex_weight_unit = fields.Selection([('LB', 'LB'),
                                          ('KG', 'KG')],
                                         default='LB')
    # Note about weight units: Odoo (v9) currently works with kilograms.
    # --> Gross weight of each products are expressed in kilograms.
    # For some services, FedEx requires weights expressed in pounds, so we
    # convert them when necessary.
    fedex_label_stock_type = fields.Selection([('PAPER_4X6', 'PAPER_4X6'),
                                               ('PAPER_4X8', 'PAPER_4X8'),
                                               ('PAPER_4X9', 'PAPER_4X9'),
                                               ('PAPER_7X4.75', 'PAPER_7X4.75'),
                                               ('PAPER_8.5X11_BOTTOM_HALF_LABEL', 'PAPER_8.5X11_BOTTOM_HALF_LABEL'),
                                               ('PAPER_8.5X11_TOP_HALF_LABEL', 'PAPER_8.5X11_TOP_HALF_LABEL'),
                                               ('PAPER_LETTER', 'PAPER_LETTER'),
                                               ('STOCK_4X6', 'STOCK_4X6'),
                                               ('STOCK_4X6.75_LEADING_DOC_TAB', 'STOCK_4X6.75_LEADING_DOC_TAB'),
                                               ('STOCK_4X6.75_TRAILING_DOC_TAB', 'STOCK_4X6.75_TRAILING_DOC_TAB'),
                                               ('STOCK_4X8', 'STOCK_4X8'),
                                               ('STOCK_4X9_LEADING_DOC_TAB', 'STOCK_4X9_LEADING_DOC_TAB'),
                                               ('STOCK_4X9_TRAILING_DOC_TAB', 'STOCK_4X9_TRAILING_DOC_TAB')],
                                             default='PAPER_LETTER')
    fedex_label_file_type = fields.Selection([('PDF', 'PDF'),
                                              ('EPL2', 'EPL2'),
                                              ('PNG', 'PNG'),
                                              ('ZPLII', 'ZPLII')],
                                             default='PDF', string="FEDEX Label File Type", oldname='x_fedex_label_file_type')

    def fedex_get_shipping_price_from_so(self, orders):
        res = []
        max_weight = _convert_weight(self.fedex_default_packaging_id.max_weight, self.fedex_weight_unit)
        for order in orders:
            price = 0.0

            # Estimate weight of the sale order; will be definitely recomputed on the picking field "weight"
            est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
            weight_value = _convert_weight(est_weight_value, self.fedex_weight_unit)

            # Some users may want to ship very lightweight items; in order to give them a rating, we round the
            # converted weight of the shipping to the smallest value accepted by FedEx: 0.01 kg or lb.
            # (in the case where the weight is actually 0.0 because weights are not set, don't do this)
            if weight_value > 0.0:
                weight_value = max(weight_value, 0.01)

            # Authentication stuff
            srm = FedexRequest(request_type="rating", prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            # Build basic rating request and set addresses
            srm.transaction_detail(order.name)
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, self.fedex_default_packaging_id.shipper_package_code, self.fedex_weight_unit)
            order_currency = order.currency_id
            srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
            srm.set_shipper(order.company_id.partner_id, order.warehouse_id.partner_id)
            srm.set_recipient(order.partner_shipping_id)

            if max_weight and weight_value > max_weight:
                total_package = int(weight_value / max_weight)
                last_package_weight = weight_value % max_weight

                for sequence in range(1, total_package + 1):
                    srm.add_package(max_weight, sequence_number=sequence, mode='rating')
                if last_package_weight:
                    total_package = total_package + 1
                    srm.add_package(last_package_weight, sequence_number=total_package, mode='rating')
                srm.set_master_package(weight_value, total_package)
            else:
                srm.add_package(weight_value, mode='rating')
                srm.set_master_package(weight_value, 1)

            request = srm.rate()

            warnings = request.get('warnings_message')
            if warnings:
                _logger.info(warnings)

            if not request.get('errors_message'):
                if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                    price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                else:
                    _logger.info("Preferred currency has not been found in FedEx response")
                    company_currency = order.company_id.currency_id
                    if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                        price = company_currency.compute(request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                    else:
                        price = company_currency.compute(request['price']['USD'], order_currency)
            else:
                raise ValidationError(request['errors_message'])

            res = res + [price]
        return res

    def fedex_send_shipping(self, pickings):
        res = []

        for picking in pickings:

            srm = FedexRequest(request_type="shipping", prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            srm.transaction_detail(picking.id)

            # FedEx forbids the use of different packagings in the same shippign
            picking.check_packages_are_identical()

            package_type = picking.package_ids and picking.package_ids[0].packaging_id.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit)
            srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
            srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
            srm.set_recipient(picking.partner_id)

            srm.shipping_charges_payment(superself.fedex_account_number)

            srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

            net_weight = _convert_weight(picking.shipping_weight, self.fedex_weight_unit)

            # Commodities for customs declaration (international shipping)
            if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY']:

                commodity_currency = order_currency
                total_commodities_amount = 0.0
                commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code

                for operation in picking.pack_operation_ids:
                    commodity_amount = order_currency.compute(operation.product_id.list_price, commodity_currency)
                    total_commodities_amount += (commodity_amount * operation.product_qty)
                    commodity_description = operation.product_id.name
                    commodity_number_of_piece = '1'
                    commodity_weight_units = self.fedex_weight_unit
                    commodity_weight_value = _convert_weight(operation.product_id.weight * operation.product_qty, self.fedex_weight_unit)
                    commodity_quantity = operation.product_qty
                    commodity_quantity_units = 'EA'
                    srm.commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units)
                srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
                srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id.country_id.code, superself.fedex_account_number)

            package_count = len(picking.package_ids) or 1

            # TODO RIM master: factorize the following crap

            ################
            # Multipackage #
            ################
            if package_count > 1:

                # Note: Fedex has a complex multi-piece shipping interface
                # - Each package has to be sent in a separate request
                # - First package is called "master" package and holds shipping-
                #   related information, including addresses, customs...
                # - Last package responses contains shipping price and code
                # - If a problem happens with a package, every previous package
                #   of the shipping has to be cancelled separately
                # (Why doing it in a simple way when the complex way exists??)

                master_tracking_id = False
                package_labels = []
                carrier_tracking_ref = ""

                for sequence, package in enumerate(picking.package_ids, start=1):

                    package_weight = _convert_weight(package.shipping_weight, self.fedex_weight_unit)
                    srm.add_package(package_weight, sequence_number=sequence)
                    srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                    request = srm.process_shipment()
                    package_name = package.name or sequence

                    warnings = request.get('warnings_message')
                    if warnings:
                        _logger.info(warnings)

                    # First package
                    if sequence == 1:
                        if not request.get('errors_message'):
                            master_tracking_id = request['master_tracking_id']
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = request['tracking_number']
                        else:
                            raise ValidationError(request['errors_message'])

                    # Intermediary packages
                    elif sequence > 1 and sequence < package_count:
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        else:
                            raise ValidationError(request['errors_message'])

                    # Last package
                    elif sequence == package_count:
                        # recuperer le label pdf
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))

                            if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                                carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                            else:
                                _logger.info("Preferred currency has not been found in FedEx response")
                                company_currency = picking.company_id.currency_id
                                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                    carrier_price = company_currency.compute(request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                                else:
                                    carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                            logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))
                            picking.message_post(body=logmessage)

                            for label in package_labels:
                                logmessage = (_("Shipping label for package %s") % (label[0]))
                                picking.message_post(body=logmessage, attachments=[('LabelFedex-%s.%s' % (label[0], self.fedex_label_file_type), label[1])])

                            shipping_data = {'exact_price': carrier_price,
                                             'tracking_number': carrier_tracking_ref}
                            res = res + [shipping_data]
                        else:
                            raise ValidationError(request['errors_message'])

            # TODO RIM handle if a package is not accepted (others should be deleted)

            ###############
            # One package #
            ###############
            elif package_count == 1:
                srm.add_package(net_weight)
                srm.set_master_package(net_weight, 1)

                # Ask the shipping to fedex
                request = srm.process_shipment()

                warnings = request.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                if not request.get('errors_message'):

                    if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                        carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                    else:
                        _logger.info("Preferred currency has not been found in FedEx response")
                        company_currency = picking.company_id.currency_id
                        if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                            carrier_price = company_currency.compute(request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                        else:
                            carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                    carrier_tracking_ref = request['tracking_number']
                    logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))

                    fedex_labels = [('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
                                    for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                    picking.message_post(body=logmessage, attachments=fedex_labels)

                    shipping_data = {'exact_price': carrier_price,
                                     'tracking_number': carrier_tracking_ref}
                    res = res + [shipping_data]
                else:
                    raise ValidationError(request['errors_message'])

            ##############
            # No package #
            ##############
            else:
                raise ValidationError(_('No packages for this picking'))

        return res

    def fedex_get_tracking_link(self, pickings):
        res = []
        for picking in pickings:
            res = res + ['https://www.fedex.com/apps/fedextrack/?action=track&trackingnumber=%s' % picking.carrier_tracking_ref]
        return res

    def fedex_cancel_shipment(self, picking):
        request = FedexRequest(request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        request.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        request.client_detail(superself.fedex_account_number, superself.fedex_meter_number)
        request.transaction_detail(picking.id)

        master_tracking_id = picking.carrier_tracking_ref.split(',')[0]
        request.set_deletion_details(master_tracking_id)
        result = request.delete_shipment()

        warnings = result.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if result.get('delete_success') and not result.get('errors_message'):
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % master_tracking_id))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})
        else:
            raise ValidationError(result['errors_message'])


def _convert_weight(weight, unit='KG'):
    ''' Convert picking weight (always expressed in KG) into the specified unit '''
    if unit == 'KG':
        return weight
    elif unit == 'LB':
        return weight / 0.45359237
    else:
        raise ValueError

def _convert_curr_fdx_iso(code):
    curr_match = {v: k for k, v in FEDEX_CURR_MATCH.items()}
    return curr_match.get(code, code)

def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)

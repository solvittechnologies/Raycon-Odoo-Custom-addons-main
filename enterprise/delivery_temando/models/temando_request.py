# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import logging
import os
import suds

from suds.client import Client
from suds.wsse import Security, UsernameToken
from urllib2 import URLError

from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
# uncomment to enable logging of SOAP requests and responses
# logging.getLogger('suds.client').setLevel(logging.DEBUG)


class TemandoRequest():
    """ Low-level object intended to interface Odoo recordsets with Temando,
        through appropriate SOAP requests """

    def __init__(self, prod_environment, username, password):
        if not prod_environment:
            wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/server.wsdl')
        else:
            wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/prod/server.wsdl')
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'))

        security = Security()
        token = UsernameToken(username, password)
        security.tokens.append(token)
        self.client.set_options(wsse=security)

    # Common stuff to rating and shipping

    def check_required_value(self, recipient, shipper, order=False, picking=False):
        required_field = ['city', 'zip', 'country_id']
        res = [field for field in required_field if not recipient[field]]
        if recipient.country_id and recipient.country_id.code in ['US', 'CA', 'AU'] and not recipient.state_id:
            res.append('state_id')
        if res:
            raise ValidationError(_("The recipient address is missing or wrong (Missing fields : %s...).") % ", ".join(res))
        res = [field for field in required_field if not shipper[field]]
        if shipper.country_id and shipper.country_id.code in ['US', 'CA', 'AU'] and not shipper.state_id:
            res.append('state_id')
        if res:
            raise ValidationError(_("The address of your company is missing or wrong (Missing fields : %s...).") % ", ".join(res))
        if order:
            if not order.order_line.filtered(lambda line: not line.is_delivery and line.product_id.type not in ['service', 'digital']):
                raise ValidationError(_("Please provide at least one item to ship."))
            for line in order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and line.product_id.type not in ['service', 'digital']):
                raise ValidationError(_('The estimated price cannot be computed because the weight of your product is missing.'))
        if picking:
            if not picking.move_lines:
                raise ValidationError(_("Please provide at least one item to ship."))
            for move in picking.move_lines.filtered(lambda move: not move.product_id.weight):
                raise ValidationError(_("The delivery cannot be done because the weight of some products is missing."))

    def set_anywhere_detail(self, carrier, shipper_partner, recipient_partner):
        self.Anywhere = self.client.factory.create('com:Anywhere')
        self.Anywhere.itemNature = carrier.temando_delivery_nature
        self.Anywhere.itemMethod = carrier.temando_delivery_type
        self.Anywhere.locationSelection = carrier.temando_location_selection
        # Shipper
        self.Anywhere.originCountry = shipper_partner.country_id.code
        self.Anywhere.originCode = shipper_partner.zip
        self.Anywhere.originSuburb = shipper_partner.city
        self.Anywhere.originCity = shipper_partner.city
        self.Anywhere.originState = shipper_partner.state_id.code or ''
        self.Anywhere.originIs = 'Business' if shipper_partner.commercial_partner_id.is_company else 'Residence'
        # Recipient
        self.Anywhere.destinationCountry = recipient_partner.country_id.code
        self.Anywhere.destinationCode = recipient_partner.zip
        self.Anywhere.destinationSuburb = recipient_partner.city
        self.Anywhere.destinationCity = recipient_partner.city
        self.Anywhere.destinationState = recipient_partner.state_id.code
        self.Anywhere.destinationIs = 'Business' if recipient_partner.commercial_partner_id.is_company else 'Residence'

    def set_general_detail(self, currency, total_price, delivery_nature):
        self.General = self.client.factory.create('com:General')
        self.General.goodsValue = total_price
        self.General.goodsCurrency = currency
        if delivery_nature == 'International':
            self.General.termsOfTrade = 'Delivered Duty Paid'

    def set_carrier_quotefilter_rating(self, carrier_id):
        self.QuoteFilter = self.client.factory.create('com:QuoteFilter')
        self.QuoteFilter.preference = 'Carrier Order'
        self.QuoteFilter.carriers = {'carrier': {'carrierId': carrier_id}}

    def set_carrier_quotefilter_detail(self, sale_order):
        self.QuoteFilter = self.client.factory.create('com:QuoteFilter')
        self.QuoteFilter.preference = 'Carrier Order'
        self.QuoteFilter.carriers = {'carrier': {'carrierId': sale_order.temando_carrier_id, 'deliveryMethods': {'deliveryMethod': sale_order.temando_delivery_method}}}

    def set_cheapest_quotefilter_detail(self):
        self.QuoteFilter = self.client.factory.create('com:QuoteFilter')
        self.QuoteFilter.preference = 'Cheapest'

    def _check_measurement_detail(self, package, carrier):
        res = {}
        if package:
            res = {'height': package.height, 'width': package.width, 'length': package.length}
        elif carrier.temando_default_packaging_id.height and carrier.temando_default_packaging_id.width and carrier.temando_default_packaging_id.length:
            res = {'height': carrier.temando_default_packaging_id.height, 'width': carrier.temando_default_packaging_id.width, 'length': carrier.temando_default_packaging_id.length}
        else:
            raise ValidationError(_('Please provide Height, Width and Length on product packaging or delivery method.'))
        return res

    # Rating

    def set_quotes_anything_detail(self, carrier, order):
        res = []

        for line in order.order_line.filtered(lambda line: not line.is_delivery and line.product_id.type not in ['service', 'digital']):
            result = self._check_measurement_detail(line.product_packaging, carrier)
            self.Anything = self.client.factory.create('com:anything')
            # always now it's for General Goods
            self.Anything['class'] = 'General Goods'
            self.Anything.subclass = carrier.temando_subclass
            self.Anything.packaging = carrier.temando_default_packaging_id.shipper_package_code
            self.Anything.palletType = carrier.temando_pallet_type or ''
            self.Anything.palletNature = carrier.temando_pallet_nature or ''
            # Packaging optimization will try to pack the Anythings together into larger boxes or packages which have been set up. Setting 'N' for packaging optimization tells our system that each Anything will be packed into a separate package
            self.Anything.packagingOptimisation = 'Y'
            # is mandatory only if:class is: Freight, General Goods or Refrigerated.
            self.Anything.qualifierFreightGeneralFragile = 'N'
            self.Anything.distanceMeasurementType = carrier.temando_distance_measurement_type
            self.Anything.weightMeasurementType = carrier.temando_weight_measurement_type
            self.Anything.length = result['length']
            self.Anything.width = result['width']
            self.Anything.height = result['height']
            self.Anything.weight = self._convert_weight(line.product_id.weight, carrier.temando_weight_measurement_type)
            self.Anything.quantity = line.product_uom_qty
            self.Anything.description = line.name
            res.append(self.Anything)
        self.Anything = {'anything': res}

    def rate_shipping(self):
        dict_response = {'price': 0.0,
                         'currency': False,
                         'carrier_id': False,
                         'carrier_name': False,
                         'delivery_method': False}
        try:
            qf = getattr(self, 'QuoteFilter', None)
            self.response = self.client.service.getQuotes(anythings=self.Anything, anywhere=self.Anywhere, general=self.General, quoteFilter=qf)

            if self.response.quotes:
                dict_response['price'] = float(self.response.quotes.quote[0].totalPrice)
                dict_response['currency'] = self.response.quotes.quote[0].currency
                dict_response['carrier_id'] = self.response.quotes.quote[0].carrier.id
                dict_response['carrier_name'] = self.response.quotes.quote[0].carrier.companyName
                dict_response['delivery_method'] = self.response.quotes.quote[0].deliveryMethod
        except suds.WebFault as fault:
            dict_response['error_message'] = fault
        except URLError:
            dict_response['error_message'] = _('Temando Server Not Found')

        return dict_response

    # Shipping

    def set_shipping_anything_detail(self, carrier, picking):
        anythings_list = []

        # Multiples packages in the picking
        for package in picking.package_ids:
            result = self._check_measurement_detail(package.packaging_id, carrier)
            self.Anything = self.client.factory.create('com:anything')
            self.Anything['class'] = 'General Goods'
            self.Anything.subclass = carrier.temando_subclass
            self.Anything.packaging = package.packaging_id.shipper_package_code or carrier.temando_default_packaging_id.shipper_package_code
            self.Anything.palletType = carrier.temando_pallet_type or ''
            self.Anything.palletNature = carrier.temando_pallet_nature or ''
            self.Anything.packagingOptimisation = 'Y'
            self.Anything.qualifierFreightGeneralFragile = 'N'
            self.Anything.distanceMeasurementType = carrier.temando_distance_measurement_type
            self.Anything.weightMeasurementType = carrier.temando_weight_measurement_type
            self.Anything.length = result['length']
            self.Anything.width = result['width']
            self.Anything.height = result['height']
            self.Anything.weight = self._convert_weight(package.shipping_weight, carrier.temando_weight_measurement_type)
            shipper_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            articles_list = []
            for po in picking.pack_operation_ids.filtered(lambda po: po.result_package_id.id == package.id):
                product_hs_code = po.product_id.hs_code or carrier.temando_hs_code
                article = self._set_article_detail(carrier, picking.picking_type_id.warehouse_id.partner_id, po.product_qty, shipper_currency.name, product_hs_code, po.product_id.name)
                articles_list = articles_list + [article]
            self.Anything.articles = articles_list
            self.Anything.quantity = len(self.Anything.articles[0]['article'])
            anythings_list = anythings_list + [self.Anything]

        # If some bulk content exists or user does not use packaging features
        if picking.weight_bulk:
            result = self._check_measurement_detail(False, carrier)
            self.Anything = self.client.factory.create('com:anything')
            self.Anything['class'] = 'General Goods'
            self.Anything.subclass = carrier.temando_subclass
            self.Anything.packaging = carrier.temando_default_packaging_id.shipper_package_code
            self.Anything.palletType = carrier.temando_pallet_type or ''
            self.Anything.palletNature = carrier.temando_pallet_nature or ''
            self.Anything.packagingOptimisation = 'Y'
            self.Anything.qualifierFreightGeneralFragile = 'N'
            self.Anything.distanceMeasurementType = carrier.temando_distance_measurement_type
            self.Anything.weightMeasurementType = carrier.temando_weight_measurement_type
            self.Anything.length = result['length']
            self.Anything.width = result['width']
            self.Anything.height = result['height']
            self.Anything.weight = self._convert_weight(picking.weight_bulk, carrier.temando_weight_measurement_type)
            shipper_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            articles_list = []
            for po in picking.pack_operation_ids:
                product_hs_code = po.product_id.hs_code or carrier.temando_hs_code
                article = self._set_article_detail(carrier, picking.picking_type_id.warehouse_id.partner_id, po.product_qty, shipper_currency.name, product_hs_code, po.product_id.name)
                articles_list = articles_list + [article]
            self.Anything.articles = articles_list
            self.Anything.quantity = 1
            anythings_list = anythings_list + [self.Anything]

        self.Anything = {'anything': anythings_list}

    def _set_article_detail(self, carrier, shipper_partner, quantity, shipper_currency, product_hs_code, product_description):
        res = []
        while (quantity):
            self.Article = self.client.factory.create('com:Article')
            self.Article.anythingIndex = int(quantity)
            self.Article.countryOfOrigin = shipper_partner.country_id.code
            self.Article.countryOfManufacture = shipper_partner.country_id.code
            self.Article.goodsCurrency = shipper_currency
            self.Article.description = product_description
            if carrier.temando_delivery_nature == 'International':
                self.Article.hs = product_hs_code
            res.append(self.Article)
            quantity = quantity - 1
        return {'article': res}

    def set_location_origin_detail(self, shipper_company_partner, shipper_warehouse_partner, shipper_warehouse):
        location_name = shipper_warehouse.temando_location
        if location_name:
            self.LocationOrigin = self.client.factory.create('com:Location')
            self.LocationOrigin.description = location_name
            self.LocationOrigin.manifesting = 'Y'
        self.LocationOrigin = self.client.factory.create('com:Location')
        self.LocationOrigin.contactName = shipper_company_partner.name
        self.LocationOrigin.companyName = shipper_company_partner.name
        self.LocationOrigin.street = ('%s %s') % (shipper_warehouse.partner_id.street or '', shipper_warehouse.partner_id.street2 or '')
        self.LocationOrigin.country = shipper_warehouse.partner_id.country_id.code
        self.LocationOrigin.code = shipper_warehouse.partner_id.zip
        self.LocationOrigin.suburb = shipper_warehouse.partner_id.city
        self.LocationOrigin.state = shipper_warehouse.partner_id.state_id.code
        self.LocationOrigin.phone1 = shipper_warehouse.partner_id.phone
        self.LocationOrigin.email = shipper_warehouse.partner_id.email

    def set_location_destination_detail(self, recipient_partner):
        self.LocationDestination = self.client.factory.create('com:Location')
        self.LocationDestination.contactName = recipient_partner.name
        self.LocationDestination.companyName = recipient_partner.name if recipient_partner.is_company else ''
        self.LocationDestination.street = ('%s %s') % (recipient_partner.street or '', recipient_partner.street2 or '')
        self.LocationDestination.suburb = recipient_partner.city
        self.LocationDestination.state = recipient_partner.state_id.code
        self.LocationDestination.code = recipient_partner.zip
        self.LocationDestination.country = recipient_partner.country_id.code
        self.LocationDestination.phone1 = recipient_partner.phone
        self.LocationDestination.fax = recipient_partner.fax or ''
        self.LocationDestination.email = recipient_partner.email or ''

    def set_payment_detail(self):
        self.Payment = self.client.factory.create('com:Payment')
        self.Payment.paymentType = 'Account'

    def set_labelprinter_detail(self, label_printer_type):
        self.LabelPrinter = self.client.factory.create('com:LabelPrinterType')
        self.LabelPrinter.labelPrinterType = label_printer_type

    def set_client_reference(self, client_id):
        self.Reference = client_id

    def make_booking(self):
        try:
            dict_response = {'tracking_number': 0.0,
                             'carrier_name': False,
                             'delivery_method': False,
                             'price': 0.0,
                             'currency': False}
            self.book_response = self.client.service.makeBooking(anythings=self.Anything, anywhere=self.Anywhere, general=self.General, origin=self.LocationOrigin, destination=self.LocationDestination, quoteFilter=self.QuoteFilter, payment=self.Payment, reference=self.Reference, labelPrinterType=self.LabelPrinter.labelPrinterType)

            dict_response['tracking_number'] = self.book_response.requestId
            dict_response['carrier_name'] = self.book_response.quote.carrier.companyName
            dict_response['delivery_method'] = self.book_response.quote.deliveryMethod
            dict_response['price'] = float(self.book_response.quote.totalPrice)
            dict_response['currency'] = self.book_response.quote.currency

        except suds.WebFault as fault:
            if fault.fault.faultcode != 'SOAP-ENV:Server':
                dict_response['error_message'] = fault
            else:
                string = fault.fault.faultstring
                dict_response['error_message'] = string[string.index('with message') + 14:string.index(':')]
        except URLError:
            dict_response['error_message'] = _('Temando Server Not Found')

        return dict_response

    def save_label(self, delivery_type):
        if delivery_type == 'International' and hasattr(self.book_response, 'commercialInvoiceDocument'):
            ascii_label_data = self.book_response.commercialInvoiceDocument
        elif hasattr(self.book_response, 'consignmentDocument'):
            ascii_label_data = self.book_response.consignmentDocument
        elif hasattr(self.book_response, 'labelDocument'):
            ascii_label_data = self.book_response.labelDocument
        else:
            return False
        label_binary_data = binascii.a2b_base64(ascii_label_data)
        return label_binary_data

    # Cancel Shipping stuff

    def set_deletion_detail(self, client_id, request_id):
        self.ClientDetail = self.client.factory.create('com:ClientReference')
        self.ClientDetail.reference = client_id
        self.CancelRequest = self.client.factory.create('xsd:positiveInteger')
        self.CancelRequest.requestId = request_id

    def cancel_shipment(self):
        dict_response = {'delete_success': False,
                         'error_message': ''}
        try:
            self.response = self.client.service.cancelRequest(self.CancelRequest.requestId)
            dict_response['ShipmentDeleted'] = True
        except suds.WebFault as fault:
            dict_response['error_message'] = fault
        except URLError:
            dict_response['error_message'] = _('Temando Server Not Found')
        return dict_response

    # Manifest stuff

    def get_manifest(self, client_id, location_name, carrier_id=0):
        dict_response = {'error_message': '',
                         'manifest_bin': None}
        try:
            self.response = self.client.service.confirmManifest(clientId=client_id, location=location_name)
            if self.response.manifestDocument:
                dict_response['manifest_bin'] = binascii.a2b_base64(self.response.manifestDocument)
            else:
                dict_response['error_message'] = _('Temando did not return any manifest')
        except suds.WebFault as fault:
            dict_response['error_message'] = fault
        except URLError:
            dict_response['error_message'] = _('Temando Server Not Found')
        return dict_response

    # Helpers

    def _convert_weight(self, weight, unit='Kilograms'):
        ''' Convert picking weight (always expressed in KG) into the specified unit '''
        units = {
            'Kilograms': 1,
            'Pounds': 2.20462,
            'Grams': 1000,
            'Ounces': 35.274
        }
        if unit in units:
            return weight * units[unit]
        else:
            raise ValueError

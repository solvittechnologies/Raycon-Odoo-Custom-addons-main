# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import time
from math import ceil
from datetime import datetime
from urllib2 import Request, urlopen, URLError
import xml.etree.ElementTree as etree
import unicodedata

from odoo import _
from odoo import release
from odoo.exceptions import ValidationError
from odoo.tools import float_repr


class DHLProvider():

    def __init__(self, prod_environment):
        if not prod_environment:
            self.url = 'https://xmlpitest-ea.dhl.com/XMLShippingServlet?isUTF8Support=true'
        else:
            self.url = 'https://xmlpi-ea.dhl.com/XMLShippingServlet?isUTF8Support=true'

    def _convert_weight(self, weight, weight_unit):
        if weight_unit == "LB":
            return round(weight * 2.20462, 3)
        else:
            return round(weight, 3)

    def _get_rate_param(self, order, carrier):
        res = {}
        total_weight = self._convert_weight(sum([(line.product_id.weight * line.product_qty) for line in order.order_line]), carrier.dhl_package_weight_unit)
        max_weight = self._convert_weight(carrier.dhl_default_packaging_id.max_weight, carrier.dhl_package_weight_unit)

        res = {
            'MessageTime': datetime.now().isoformat(),
            'MessageReference': 'ref:' + datetime.now().isoformat(),
            'carrier': carrier,
            'shipper_partner': order.warehouse_id.partner_id,
            'Date': time.strftime('%Y-%m-%d'),
            'ReadyTime': time.strftime('PT%HH%MM'),
            'recipient_partner': order.partner_shipping_id,
            'total_weight': total_weight,
            'currency_name': order.currency_id.name,
            'total_value': str(float_repr(sum([(line.price_unit * line.product_uom_qty) for line in order.order_line.filtered(lambda line: not line.is_delivery)]), 2)),
            'is_dutiable': carrier.dhl_dutiable,
            'package_ids': False,
        }
        if max_weight and total_weight > max_weight:
            total_package = int(ceil(total_weight / max_weight))
            last_package_weight = total_weight % max_weight
            res['total_packages'] = total_package
            res['last_package_weight'] = last_package_weight
            res['package_ids'] = carrier.dhl_default_packaging_id
        return res

    def rate_request(self, order, carrier):
        dict_response = {'price': 0.0,
                         'currency': False,
                         'error_found': False}

        param = self._get_rate_param(order, carrier)
        request_text = self._create_rate_xml(param)
        root = self._send_request(request_text)
        if root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition')
            error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            raise ValidationError(_(error_msg))

        elif root.tag == '{http://www.dhl.com}DCTResponse':
            condition = root.findall('GetQuoteResponse/Note/Condition')
            if condition:
                error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
                raise ValidationError(_(error_msg))

            products = root.findall('GetQuoteResponse/BkgDetails/QtdShp')
            found = False
            for product in products:
                if product.findtext('GlobalProductCode') == carrier.dhl_product_code\
                        and product.findall('ShippingCharge'):
                    dict_response['price'] = product.findall('ShippingCharge')[0].text
                    dict_response['currency'] = product.findall('QtdSInAdCur/CurrencyCode')[0].text
                    found = True
            if not found:
                raise ValidationError(_("No shipping available for the selected DHL product"))
        return dict_response

    def _get_send_param(self, picking, carrier):
        return {
            # it's if you want to track the message numbers
            'MessageTime': datetime.now().isoformat(),
            'MessageReference': 'ref:' + datetime.now().isoformat(),
            'carrier': carrier,
            'RegionCode': carrier.dhl_region_code,
            'lang': 'en',
            'recipient_partner': picking.partner_id,
            'PiecesEnabled': 'Y',
            # Hard coded, S for Shipper, R for Recipient and T for Third Party
            'ShippingPaymentType': 'S',
            'recipient_streetLines': ('%s%s') % (picking.partner_id.street or '',
                                                 picking.partner_id.street2 or ''),
            'NumberOfPieces': len(picking.package_ids) or 1,
            'weight_bulk': self._convert_weight(picking.weight_bulk, carrier.dhl_package_weight_unit),
            'package_ids': picking.package_ids,
            'total_weight': self._convert_weight(picking.shipping_weight, carrier.dhl_package_weight_unit),
            'weight_unit': carrier.dhl_package_weight_unit[:1],
            'dimension_unit': carrier.dhl_package_dimension_unit[0],
            # For the rating API waits for CM and IN here for C and I...
            'GlobalProductCode': carrier.dhl_product_code,
            'Date': time.strftime('%Y-%m-%d'),
            'shipper_partner': picking.picking_type_id.warehouse_id.partner_id,
            'shipper_company': picking.company_id,
            'shipper_streetLines': ('%s%s') % (picking.picking_type_id.warehouse_id.partner_id.street or '',
                                               picking.picking_type_id.warehouse_id.partner_id.street2 or ''),
            'LabelImageFormat': carrier.dhl_label_image_format,
            'LabelTemplate': carrier.dhl_label_template,
            'is_dutiable': carrier.dhl_dutiable,
            'currency_name': picking.sale_id.currency_id.name or picking.company_id.currency_id.name,
            'total_value': str(float_repr(sum([line.product_id.lst_price * int(line.product_uom_qty) for line in picking.move_lines]), 2))
        }

    def _get_send_param_final_rating(self, picking, carrier):
        return {
            'MessageTime': datetime.now().isoformat(),
            'MessageReference': 'ref:' + datetime.now().isoformat(),
            'carrier': carrier,
            'shipper_partner': picking.picking_type_id.warehouse_id.partner_id,
            'Date': time.strftime('%Y-%m-%d'),
            'ReadyTime': time.strftime('PT%HH%MM'),
            'recipient_partner': picking.partner_id,
            'currency_name': picking.sale_id.currency_id.name or picking.company_id.currency_id.name,
            'total_value': str(float_repr(sum([line.product_id.lst_price * int(line.product_uom_qty) for line in picking.move_lines]), 2)),
            'is_dutiable': carrier.dhl_dutiable,
            'package_ids': picking.package_ids,
            'total_weight': self._convert_weight(picking.weight_bulk, carrier.dhl_package_weight_unit),
        }

    def send_shipping(self, picking, carrier):
        dict_response = {'tracking_number': 0.0,
                         'price': 0.0,
                         'currency': False}

        param = self._get_send_param(picking, carrier)
        request_text = self._create_shipping_xml(param)

        root = self._send_request(request_text)
        if root.tag == '{http://www.dhl.com}ShipmentValidateErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            error_msg = "%s: %s" % (condition[1].text, condition[0].text)
            raise ValidationError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            if isinstance(condition[0], list):
                error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            else:
                error_msg = "%s: %s" % (condition[0].text, condition[1].text)
            raise ValidationError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}ShipmentResponse':
            label_image = root.findall('LabelImage')
            self.label = label_image[0].findall('OutputImage')[0].text
            dict_response['tracking_number'] = root.findtext('AirwayBillNumber')

        # Warning sometimes the ShipmentRequest returns a shipping rate, not everytime.
        # After discussing by mail with the DHL Help Desk, they said that the correct rate
        # is given by the DCTRequest GetQuote.

        param_final_rating = self._get_send_param_final_rating(picking, carrier)
        request_text = self._create_rate_xml(param_final_rating)
        root = self._send_request(request_text)
        if root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            raise ValidationError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}DCTResponse':
            products = root.findall('GetQuoteResponse/BkgDetails/QtdShp')
            found = False
            for product in products:
                if product.findtext('GlobalProductCode') == carrier.dhl_product_code\
                        and product.findall('ShippingCharge'):
                    dict_response['price'] = product.findall('ShippingCharge')[0].text
                    dict_response['currency'] = product.findall('QtdSInAdCur/CurrencyCode')[0].text
                    found = True
            if not found:
                raise ValidationError(_("No service available for the selected product"))

        return dict_response

    def save_label(self):
        label_binary_data = binascii.a2b_base64(self.label)
        return label_binary_data

    def send_cancelling(self, picking, carrier):
        dict_response = {'tracking_number': 0.0, 'price': 0.0, 'currency': False}
        return dict_response

    def _send_request(self, request_xml):
        try:
            req = Request(url=self.url,
                          data=request_xml,
                          headers={'Content-Type': 'application/xml'})
            response_text = urlopen(req).read()
        except URLError:
            raise ValidationError("DHL Server not found. Check your connectivity.")
        root = etree.fromstring(response_text)
        return root

    def _create_rate_xml(self, param):
        carrier = param["carrier"].sudo()
        etree.register_namespace("req", "http://www.dhl.com")
        root = etree.Element("{http://www.dhl.com}DCTRequest")
        root.attrib['schemaVersion'] = "2.0"
        get_quote_node = etree.SubElement(root, "GetQuote")
        request_node = etree.SubElement(get_quote_node, "Request")
        service_header_node = etree.SubElement(request_node, "ServiceHeader")
        etree.SubElement(service_header_node, "MessageTime").text = param['MessageTime']
        etree.SubElement(service_header_node, "MessageReference").text = param['MessageReference']
        etree.SubElement(service_header_node, "SiteID").text = carrier.dhl_SiteID
        etree.SubElement(service_header_node, "Password").text = carrier.dhl_password

        metadata_node = etree.SubElement(request_node, "MetaData")
        etree.SubElement(metadata_node, "SoftwareName").text = release.product_name
        etree.SubElement(metadata_node, "SoftwareVersion").text = release.series

        from_node = etree.SubElement(get_quote_node, "From")
        etree.SubElement(from_node, "CountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(from_node, "Postalcode").text = param["shipper_partner"].zip
        etree.SubElement(from_node, "City").text = param["shipper_partner"].city

        bkg_details_node = etree.SubElement(get_quote_node, "BkgDetails")
        etree.SubElement(bkg_details_node, "PaymentCountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(bkg_details_node, "Date").text = param["Date"]
        etree.SubElement(bkg_details_node, "ReadyTime").text = param["ReadyTime"]
        etree.SubElement(bkg_details_node, "DimensionUnit").text = carrier.dhl_package_dimension_unit
        etree.SubElement(bkg_details_node, "WeightUnit").text = carrier.dhl_package_weight_unit
        pieces_node = etree.SubElement(bkg_details_node, "Pieces")
        if param["package_ids"] and not param.get('total_packages'):
            for index, package in enumerate(param["package_ids"], start=1):
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(index)
                packaging = package.packaging_id or carrier.dhl_default_packaging_id
                etree.SubElement(piece_node, "PackageTypeCode").text = packaging.shipper_package_code
                etree.SubElement(piece_node, "Height").text = str(packaging.height)
                etree.SubElement(piece_node, "Depth").text = str(packaging.length)
                etree.SubElement(piece_node, "Width").text = str(packaging.width)
                etree.SubElement(piece_node, "Weight").text = str(package.shipping_weight)
        elif param['package_ids'] and param.get('total_packages'):
            package = param['package_ids']
            for seq in range(1, param['total_packages'] + 1):
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(seq)
                etree.SubElement(piece_node, "PackageTypeCode").text = package.shipper_package_code
                etree.SubElement(piece_node, "Height").text = str(package.height)
                etree.SubElement(piece_node, "Depth").text = str(package.length)
                etree.SubElement(piece_node, "Width").text = str(package.width)
                if seq == param['total_packages'] and param['last_package_weight']:
                    etree.SubElement(piece_node, "Weight").text = str(param['last_package_weight'])
                else:
                    etree.SubElement(piece_node, "Weight").text = str(package.max_weight)
        else:
            piece_node = etree.SubElement(pieces_node, "Piece")
            etree.SubElement(piece_node, "PieceID").text = str(1)
            packaging = carrier.dhl_default_packaging_id
            etree.SubElement(piece_node, "PackageTypeCode").text = packaging.shipper_package_code
            etree.SubElement(piece_node, "Height").text = str(packaging.height)
            etree.SubElement(piece_node, "Depth").text = str(packaging.length)
            etree.SubElement(piece_node, "Width").text = str(packaging.width)
            etree.SubElement(piece_node, "Weight").text = str(param["total_weight"])

        etree.SubElement(bkg_details_node, "PaymentAccountNumber").text = carrier.dhl_account_number
        if param["is_dutiable"]:
            etree.SubElement(bkg_details_node, "IsDutiable").text = "Y"
        else:
            etree.SubElement(bkg_details_node, "IsDutiable").text = "N"
        etree.SubElement(bkg_details_node, "NetworkTypeCode").text = 'AL'
        to_node = etree.SubElement(get_quote_node, "To")
        etree.SubElement(to_node, "CountryCode").text = param["recipient_partner"].country_id.code
        etree.SubElement(to_node, "Postalcode").text = param["recipient_partner"].zip
        etree.SubElement(to_node, "City").text = param["recipient_partner"].city

        if param["is_dutiable"]:
            dutiable_node = etree.SubElement(get_quote_node, "Dutiable")
            etree.SubElement(dutiable_node, "DeclaredCurrency").text = param["currency_name"]
            etree.SubElement(dutiable_node, "DeclaredValue").text = str(round(param["total_value"], 2))
        return etree.tostring(root)

    def _create_shipping_xml(self, param):
        carrier = param["carrier"].sudo()
        etree.register_namespace("req", "http://www.dhl.com")
        root = etree.Element("{http://www.dhl.com}ShipmentRequest")
        root.attrib['schemaVersion'] = "6.2"
        root.attrib['xsi:schemaLocation'] = "http://www.dhl.com ship-val-global-req-6.2.xsd"
        root.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

        request_node = etree.SubElement(root, "Request")
        service_header_node = etree.SubElement(request_node, "ServiceHeader")
        etree.SubElement(service_header_node, "MessageTime").text = param["MessageTime"]
        etree.SubElement(service_header_node, "MessageReference").text = param["MessageReference"]
        etree.SubElement(service_header_node, "SiteID").text = carrier.dhl_SiteID
        etree.SubElement(service_header_node, "Password").text = carrier.dhl_password

        metadata_node = etree.SubElement(request_node, "MetaData")
        etree.SubElement(metadata_node, "SoftwareName").text = release.product_name
        etree.SubElement(metadata_node, "SoftwareVersion").text = release.series

        etree.SubElement(root, "RegionCode").text = param["RegionCode"]
        etree.SubElement(root, "RequestedPickupTime").text = "Y"

        etree.SubElement(root, "LanguageCode").text = param["lang"]
        etree.SubElement(root, "PiecesEnabled").text = param["PiecesEnabled"]

        billing_node = etree.SubElement(root, "Billing")
        etree.SubElement(billing_node, "ShipperAccountNumber").text = carrier.dhl_account_number
        etree.SubElement(billing_node, "ShippingPaymentType").text = param['ShippingPaymentType']
        if param["is_dutiable"]:
            # S:Shipper, R:Recipient, T:Third Party.
            etree.SubElement(billing_node, "DutyPaymentType").text = carrier.env['ir.config_parameter'].get_param("delivery_dhl.duty_payment_type", "S")

        consignee_node = etree.SubElement(root, "Consignee")
        etree.SubElement(consignee_node, "CompanyName").text = self._remove_accents(param["recipient_partner"].name)
        etree.SubElement(consignee_node, "AddressLine").text = self._remove_accents(param["recipient_streetLines"])
        etree.SubElement(consignee_node, "City").text = self._remove_accents(param["recipient_partner"].city)

        if param["recipient_partner"].state_id:
            etree.SubElement(consignee_node, "Division").text = param["recipient_partner"].state_id.name
            etree.SubElement(consignee_node, "DivisionCode").text = param["recipient_partner"].state_id.code
        etree.SubElement(consignee_node, "PostalCode").text = param["recipient_partner"].zip
        etree.SubElement(consignee_node, "CountryCode").text = param["recipient_partner"].country_id.code
        etree.SubElement(consignee_node, "CountryName").text = param["recipient_partner"].country_id.name
        contact_node = etree.SubElement(consignee_node, "Contact")
        etree.SubElement(contact_node, "PersonName").text = self._remove_accents(param["recipient_partner"].name)
        etree.SubElement(contact_node, "PhoneNumber").text = param["recipient_partner"].phone or 'NA'
        etree.SubElement(contact_node, "Email").text = param["recipient_partner"].email
        if param["is_dutiable"]:
            dutiable_node = etree.SubElement(root, "Dutiable")
            etree.SubElement(dutiable_node, "DeclaredValue").text = param["total_value"]
            etree.SubElement(dutiable_node, "DeclaredCurrency").text = param["currency_name"]

        shipment_details_node = etree.SubElement(root, "ShipmentDetails")
        etree.SubElement(shipment_details_node, "NumberOfPieces").text = str(param["NumberOfPieces"])
        pieces_node = etree.SubElement(shipment_details_node, "Pieces")
        if param["package_ids"]:
            # Multi-package
            for package in param["package_ids"]:
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(package.name)   # need to be removed
                packaging = package.packaging_id or carrier.dhl_default_packaging_id
                etree.SubElement(piece_node, "Width").text = str(packaging.width)
                etree.SubElement(piece_node, "Height").text = str(packaging.height)
                etree.SubElement(piece_node, "Depth").text = str(packaging.length)
                etree.SubElement(piece_node, "PieceContents").text = str(package.name)
        if param["weight_bulk"]:
            # Monopackage
            packaging = carrier.dhl_default_packaging_id
            piece_node = etree.SubElement(pieces_node, "Piece")
            etree.SubElement(piece_node, "PieceID").text = str(1)   # need to be removed
            etree.SubElement(piece_node, "Width").text = str(packaging.width)
            etree.SubElement(piece_node, "Height").text = str(packaging.height)
            etree.SubElement(piece_node, "Depth").text = str(packaging.length)
        etree.SubElement(shipment_details_node, "Weight").text = str(param["total_weight"])
        etree.SubElement(shipment_details_node, "WeightUnit").text = param["weight_unit"]
        etree.SubElement(shipment_details_node, "GlobalProductCode").text = param["GlobalProductCode"]
        etree.SubElement(shipment_details_node, "LocalProductCode").text = param["GlobalProductCode"]
        etree.SubElement(shipment_details_node, "Date").text = param["Date"]
        etree.SubElement(shipment_details_node, "Contents").text = "MY DESCRIPTION"
        etree.SubElement(shipment_details_node, "DimensionUnit").text = param["dimension_unit"]
        etree.SubElement(shipment_details_node, "CurrencyCode").text = param["currency_name"]

        shipper_node = etree.SubElement(root, "Shipper")
        etree.SubElement(shipper_node, "ShipperID").text = carrier.dhl_account_number
        etree.SubElement(shipper_node, "CompanyName").text = self._remove_accents(param["shipper_company"].name)
        etree.SubElement(shipper_node, "AddressLine").text = self._remove_accents(param["shipper_streetLines"])
        etree.SubElement(shipper_node, "City").text = self._remove_accents(param["shipper_partner"].city)
        etree.SubElement(shipper_node, "PostalCode").text = self._remove_accents(param["shipper_partner"].zip)
        etree.SubElement(shipper_node, "CountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(shipper_node, "CountryName").text = param["shipper_partner"].country_id.name

        contact_node = etree.SubElement(shipper_node, "Contact")
        etree.SubElement(contact_node, "PersonName").text = self._remove_accents(param["shipper_partner"].name)
        etree.SubElement(contact_node, "PhoneNumber").text = param["shipper_partner"].phone

        etree.SubElement(root, "LabelImageFormat").text = param["LabelImageFormat"]

        label_node = etree.SubElement(root, "Label")
        etree.SubElement(label_node, "LabelTemplate").text = param["LabelTemplate"]

        return etree.tostring(root)

    def check_required_value(self, carrier, recipient, shipper, order=False, picking=False):
        carrier = carrier.sudo()
        recipient_required_field = ['city', 'zip', 'country_id']
        if not carrier.dhl_SiteID:
            raise ValidationError(_("DHL Site ID is missing, please modify your delivery method settings."))
        if not carrier.dhl_password:
            raise ValidationError(_("DHL password is missing, please modify your delivery method settings."))
        if not carrier.dhl_account_number:
            raise ValidationError(_("DHL account number is missing, please modify your delivery method settings."))

        if not recipient.street and not recipient.street2:
            recipient_required_field.append('street')
        res = [field for field in recipient_required_field if not recipient[field]]
        if res:
            raise ValidationError(_("The address of the custommer is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", ""))

        shipper_required_field = ['city', 'zip', 'phone', 'country_id']
        if not shipper.street and not shipper.street2:
            shipper_required_field.append('street')

        res = [field for field in shipper_required_field if not shipper[field]]
        if res:
            raise ValidationError(_("The address of your company warehouse is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", ""))

        if order:
            if not order.order_line:
                raise ValidationError(_("Please provide at least one item to ship."))
            for line in order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and not line.product_id.type in ['service', 'digital']):
                raise ValidationError(_('The estimated price cannot be computed because the weight of your product is missing.'))
        return True

    def _remove_accents(self, input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nfkd_form.encode('ASCII', 'ignore')
        return only_ascii

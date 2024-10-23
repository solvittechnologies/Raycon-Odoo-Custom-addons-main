# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from usps_request import USPSRequest


class ProviderUSPS(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('usps', "USPS")])
    # Fields required to configure
    usps_username = fields.Char(string='USPS User ID', groups="base.group_system")
    usps_account_validated = fields.Boolean(string="Account Validated", help="Check this box if your account is validated by USPS")
    usps_delivery_nature = fields.Selection([('domestic', 'Domestic'),
                                             ('international', 'International')],
                                            string="Delivery Nature", default='domestic', required=True)
    usps_size_container = fields.Selection([('LARGE', 'Large'),
                                            ('REGULAR', 'Regular')],
                                           default='REGULAR', store=True, compute='_compute_size_container')

    @api.one
    @api.depends('usps_container')
    def _compute_size_container(self):
        if self.usps_container == 'VARIABLE':
            self.usps_size_container = 'REGULAR'
        else:
            self.usps_size_container = 'LARGE'

    usps_label_file_type = fields.Selection([('PDF', 'PDF'),
                                             ('TIF', 'TIF')],
                                            string="USPS Label File Type", default='PDF')
    usps_service = fields.Selection([('First-Class', 'First-Class'),
                                     ('Priority', 'Priority'),
                                     ('Express', 'Express')],
                                    required=True, string="USPS Service", default="Express")
    usps_first_class_mail_type = fields.Selection([('LETTER', 'Letter'),
                                                   ('FLAT', 'Flat'),
                                                   ('PARCEL', 'Parcel'),
                                                   ('POSTCARD', 'Postcard'),
                                                   ('PACKAGE SERVICE', 'Package Service')],
                                                  string="USPS First Class Mail Type", default="LETTER")
    usps_container = fields.Selection([('VARIABLE', 'Regular < 12 inch'),
                                       ('RECTANGULAR', 'Rectangular'),
                                       ('NONRECTANGULAR', 'Non-rectangular')],
                                      required=True, default='VARIABLE', string="Type of container")
    usps_domestic_regular_container = fields.Selection([('Flat Rate Envelope', 'Flat Rate Envelope'),
                                                        ('Sm Flat Rate Envelope', 'Small Flat Rate Envelope'),
                                                        ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
                                                        ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
                                                        ('Flat Rate Box', 'Flat Rate Box'),
                                                        ('Sm Flat Rate Box', 'Small Flat Rate Box'),
                                                        ('Lg Flat Rate Box', 'Large Flat Rate Box'),
                                                        ('Md Flat Rate Box', 'Medium Flat Rate Box')],
                                                       string="Type of USPS domestic regular container", default="Lg Flat Rate Box")

    # For international shipping
    usps_international_regular_container = fields.Selection([('FLATRATEENV', 'Flat Rate Envelope'),
                                                             ('LEGALFLATRATEENV', 'Legal Flat Rate Envelope'),
                                                             ('PADDEDFLATRATEENV', 'Padded Flat Rate Envelope'),
                                                             ('FLATRATEBOX', 'Flat Rate Box')],
                                                            string="Type of USPS International regular container", default="FLATRATEBOX")
    usps_mail_type = fields.Selection([('Package', 'Package'),
                                       ('Letter', 'Letter'),
                                       ('FlatRate', 'Flat Rate'),
                                       ('FlatRateBox', 'Flat Rate Box'),
                                       ('LargeEnvelope', 'Large Envelope')],
                                      default="FlatRateBox", string="USPS Mail Type")
    usps_content_type = fields.Selection([('SAMPLE', 'Sample'),
                                          ('GIFT', 'Gift'),
                                          ('DOCUMENTS', 'Documents'),
                                          ('RETURN', 'Return'),
                                          ('MERCHANDISE', 'Merchandise')],
                                         default='MERCHANDISE', string="Content Type")
    usps_custom_container_width = fields.Float(string='Package width (in inches)')
    usps_custom_container_length = fields.Float(string='Package length (in inches)')
    usps_custom_container_height = fields.Float(string='Package height (in inches)')
    usps_custom_container_girth = fields.Float(string='Package girth (in inches)')
    usps_intl_non_delivery_option = fields.Selection([('RETURN', 'Return'),
                                                      ('REDIRECT', 'Redirect'),
                                                      ('ABANDON', 'Abandon')],
                                                     default="ABANDON", string="Non delivery option")
    usps_redirect_partner_id = fields.Many2one('res.partner', string="Redirect Partner")
    usps_machinable = fields.Boolean(string="Machinable", help="Please check on USPS website to ensure that your package is machinable.")

    def usps_get_shipping_price_from_so(self, orders):
        res = []
        srm = USPSRequest(self.prod_environment)

        for order in orders:
            srm.check_required_value(order.partner_shipping_id, order.carrier_id.usps_delivery_nature, order.warehouse_id.partner_id, order=order)

            quotes = srm.usps_rate_request(order, self)
            if quotes.get('error_message'):
                raise ValidationError(quotes['error_message'])

            # USPS always returns prices in USD
            if order.currency_id.name == 'USD':
                price = quotes['price']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                price = quote_currency.compute(quotes['price'], order.currency_id)

            res = res + [price]
        return res

    def usps_send_shipping(self, pickings):
        res = []
        srm = USPSRequest(self.prod_environment)
        for picking in pickings:
            srm.check_required_value(picking.partner_id, self.usps_delivery_nature, picking.picking_type_id.warehouse_id.partner_id, picking=picking)
            booking = srm.usps_request(picking, self.usps_delivery_nature, self.usps_service)

            if booking.get('error_message'):
                raise ValidationError(booking['error_message'])

            currency_order = picking.sale_id.currency_id
            if not currency_order:
                currency_order = picking.company_id.currency_id

            # USPS always returns prices in USD
            if currency_order.name == "USD":
                price = booking['price']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', "USD")], limit=1)
                price = quote_currency.compute(booking['price'], currency_order)

            carrier_tracking_ref = booking['tracking_number']

            logmessage = (_("Shipment created into USPS <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))
            picking.message_post(body=logmessage, attachments=[('LabelUSPS-%s.%s' % (carrier_tracking_ref, self.usps_label_file_type), booking['label'])])

            shipping_data = {'exact_price': price,
                             'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
        return res

    def usps_get_tracking_link(self, pickings):
        res = []
        for picking in pickings:
            res = res + ['https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=%s' % (picking.carrier_tracking_ref)]
        return res

    def usps_cancel_shipment(self, picking):

        srm = USPSRequest(self.prod_environment)

        result = srm.cancel_shipment(picking, self.usps_account_validated)

        if result['error_found']:
            raise ValidationError(result['error_message'])
        else:
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % picking.carrier_tracking_ref))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})

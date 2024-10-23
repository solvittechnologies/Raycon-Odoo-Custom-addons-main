from odoo import models, fields, api, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils



class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'


    complaints = fields.Text('Complaints/Escalations')




class SaleQuotationInherit(models.Model):
    _inherit = 'sale.order'
    _rec_name = 'quote_name'

    def action_quote_sent(self):
        for rec in self:
            rec.state = 'to_accept'

    def action_to_accept(self):
        for rec in self:
            rec.state = 'to_accept'

    def action_waiting(self):
        for rec in self:
            rec.state = 'waiting'
            users = self.env.ref('sales_team.group_sale_manager').users
            for user in users:
                rec.message_post(                                                                                                                                                         
                body="A Quotation is Awaiting Approval",                                                                                                                              
                partner_ids=[user.partner_id.id],                                                                                                                                
                message_type= "notification",                                                                                                                                        
                subtype_id=  self.env.ref("mail.mt_comment").id,                                                                                                               
                record_name= rec.name,                                                                                                                                          
                subject= _("Quotation Awaiting Approval"),                                                                                                                               
                model=self._name,                                                                                                                                                    
                res_id= rec.id                                                                                                                                                         
              )

    def action_quote_approve(self):
        for rec in self:
            rec.state = 'quote_approved'

    def action_send_to_cust(self):
        for rec in self:
            rec.state = 'sent'

    def action_quote_disapprove(self):
        for rec in self:
            rec.state = 'draft'

    def action_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        lang = self.env.context.get('lang')
        template = template_id and self.env['mail.template'].browse(template_id)
        if template and template.lang:
            lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'model_description': self.with_context(lang=lang).type_name,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'quote_approved').with_context(tracking_disable=True).write({'state': 'sent'})
            self.env.user.company_id.set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        return super(SaleQuotationInherit, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


    @api.model
    def create(self, vals):
        if vals.get('quote_name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['quote_name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id'])\
                    .next_by_code('quote.sequence') or _('New')
            else:
                vals['quote_name'] = self.env['ir.sequence'].next_by_code('quote.sequence') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.
                                                   property_product_pricelist.id)
        result = super(SaleQuotationInherit, self).create(vals)
        return result

    @api.onchange('partner_id')
    def partner_id_domainn(self):
        for rec in self:
            return {'domain': {'branches': [('branch_id', '=', rec.partner_id.id)]}}


    @api.onchange('order_line')
    def compute_profit(self):
        for rec in self:
            cost_price = 0
            selling_price = 0
            for line in rec.order_line:
                cost_price +=line.purchase_price
                selling_price +=line.price_unit
            rec.total_cost = cost_price
            rec.gross_profit = selling_price - cost_price


    state = fields.Selection([
        ('draft', 'Quotation'),
        ('to_accept', 'Quote Awaiting Approval'),
        ('quote_approved', 'Approved Quotations'),
        ('sent', 'Quote Awaiting Conversion to Sales Order'),
        ('waiting', 'Quote Awaiting Conversion to SO'),
        ('sale', 'Sale Order Approved'),
        ('no_sale', 'Sale Order Disapproved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, track_visibility='onchange', default='draft')
    # date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
    #                              states={'draft': [('readonly', False), ('required', False)],
    #                                      'sent': [('readonly', False)], 'waiting': [('readonly', False)],
    #                                      'so_to_approve': [('readonly', True)]}, copy=False)
    #
    # quote_no = fields.Char('Quote No')
    date_quote = fields.Datetime(string='Quote Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    sale_shipping_term_id = fields.Many2one('sale.shipping.term', string='Shipping Term')
    quote_name = fields.Char(string='Quote No', required=True, copy=False, readonly=True,
                             states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    so_name = fields.Char('SO Name')
    branches = fields.Many2one('company.branch', string='Branch')
    subject = fields.Char(string = 'Quote Subject')
    contact_person = fields.Many2one('res.partner', string='Contact')
    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines')
    total_cost = fields.Float(string="Total Cost",readonly=True,store=True)
    gross_profit = fields.Float(string="Gross Profit",readonly=True,store=True)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('purchase_price', 'product_uom_qty')
    def _total_cost_price(self):
        for rec in self:
            rec.total_purchase_price = rec.purchase_price * rec.product_uom_qty

    @api.depends('margin', 'total_purchase_price')
    def _product_margin(self):
        for rec in self:
            # if rec.margin:
            rec.profit = rec.price_subtotal - rec.total_purchase_price

    # @api.depends('purchase_price', 'margin')
    # def _sell_price(self):
    #     for rec in self:
    #         if rec.purchase_price:
    #             rec.price_unit = rec.purchase_price / (1 - (rec.margin / 100))

    @api.depends('price_unit', 'product_uom_qty')
    def _total_selling_price(self):
        for rec in self:
            rec.total_sell_unit_price = rec.price_unit * rec.product_uom_qty

    @api.onchange('price_unit')
    def compute_margin(self):
        for rec in self:
            if rec.price_unit and rec.purchase_price:
                margin_decimal = (rec.price_unit - rec.purchase_price)/rec.price_unit 
                rec.margin = margin_decimal * 100

    def _get_defalt_margin(self):
        default_margin = 18
        return default_margin

    def _get_user_groups(self):
        if self.env.user.has_group('base.group_erp_manager'):
            return True
        return False

    @api.onchange('product_id')
    def _get_categ(self):
        for rec in self:
            if rec.product_id:
                rec.product_cat = rec.product_id.categ_id.name


    @api.onchange('product_id')
    def _get_p_type(self):
        for rec in self:
            if rec.product_id:
                rec.p_type = rec.product_id.p_type.name

    @api.onchange('product_id')
    def product_id_domainn(self):
        for rec in self:
            return {'domain': {'product_desc': [('description_id', '=', rec.product_id.id)]}}
   
    @api.onchange('product_desc')
    def product_description_onchange(self):
        for rec in self:
            rec.name = rec.product_id.name+" ("+str(rec.product_desc.name)+")" if rec.product_id else ''

    # can_edit_margin = fields.(_get_user_groups, type='boolean', relation='res.groups',
    #                 string='Groups')
    p_type = fields.Text(string='Type')
    product_cat = fields.Text(string='Category', required=False)
    product_desc = fields.Many2many('product.description', string='Description')
    margin = fields.Float(string='Margin(%)', default=_get_defalt_margin)
    profit = fields.Float(string='Margin', compute='_product_margin', store=True)
    purchase_price = fields.Float('Cost', readonly=False)
    total_purchase_price = fields.Float('Total Cost', compute='_total_cost_price', readonly=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
#    sell_price_unit = fields.Float('Unit Price', compute="_sell_price")
    total_sell_unit_price = fields.Float('TSP', compute="_total_selling_price")


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: not inv.partner_id):
            raise UserError(_("The field Vendor is required, please complete it to validate the Vendor Bill."))
        if to_open_invoices.filtered(lambda inv: inv.state != 'inv_to_approve'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(
                lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        if to_open_invoices.filtered(lambda inv: not inv.account_id):
            raise UserError(
                _('No account was found to create the invoice, be sure you have installed a chart of account.'))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if invoice.partner_id not in invoice.message_partner_ids:
                invoice.message_subscribe([invoice.partner_id.id])

            # Auto-compute reference, if not already existing and if configured on company
            if not invoice.reference and invoice.type == 'out_invoice':
                invoice.reference = invoice._get_computed_reference()

            # DO NOT FORWARD-PORT.
            # The reference is copied after the move creation because we need the move to get the invoice number but
            # we need the invoice number to get the reference.
            invoice.move_id.ref = invoice.reference
        self._check_duplicate_supplier_reference()

        return self.write({'state': 'open'})

    def action_to_inv_approve(self):
        for rec in self:
            rec.state = 'inv_to_approve'
            #mail account manager group

            #get users in account manager group
            users = self.env.ref('account.group_account_manager').users

            for user in users:
                rec.message_post(
                    body="An Invoice is Awaiting Approval",
                    partner_ids=[user.partner_id.id],
                    message_type= "notification",
                    subtype_id=  self.env.ref("mail.mt_comment").id,
                    record_name= rec.name,
                    subject= _("Invoice Awaiting Approval"),
                    model=self._name,
                    res_id= rec.id
                    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('inv_to_approve', 'To Approve'),
        ('open', 'Open'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_rfq_send(self):
        for rec in self:
            rec.state = 'to approve'

    def button_approve(self, force=False):
        result = super(PurchaseOrder, self).button_approve(force=force)
        self._create_picking()
        for rec in self:
            rec.state = 'sent'
        return result  
  
    def button_disapprove(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
                order.write({'state': 'purchase'}) 
                users = self.env.ref('account.group_account_invoice').users
                for user in users:
                    order.message_post(                                                                                                                                                         
                         body="A new purchase order is awaiting payment",                                                                                                                              
                         partner_ids=[user.partner_id.id],                                                                                                                                
                         message_type= "notification",                                                                                                                                        
                         subtype_id=  self.env.ref("mail.mt_comment").id,                                                                                                               
                         record_name= order.name,                                                                                                                                          
                         subject= _("Purchase order awaiting payment"),                                                                                                                               
                         model=self._name,                                                                                                                                                    
                         res_id= order.id                                                                                                                                                         
                         )               
            else:
                order.write({'state': 'to approve'})
        return True


    state = fields.Selection([
        ('draft', 'RFQ'),
        ('to approve', 'To Approve'),
        ('sent', 'RFQ Sent'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
  


class ProductType(models.Model):
    _name = "product.type"

    name = fields.Char(string="Type")


class ProductDescription(models.Model):
    _name = "product.description"

    name = fields.Char(string="Description")
    description_id = fields.Many2one('product.template', string='Related Product')


class ProductInherit(models.Model):
    _inherit = 'product.template'

    p_type = fields.Many2one('product.type', string="Type")
    p_desc = fields.One2many('product.description', 'description_id', string='Descriptions')

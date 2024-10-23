# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrintOrderWizard(models.TransientModel):
    """ This wizard aims to generate the print order relative to the selected 'printable' objects (account.invoice,
        sale.order, ...).
    """

    _name = 'print.order.wizard'
    _description = 'Print Order Wizard'
    _rec_name = 'id'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_print_provider(self):
        return self.env['ir.values'].get_default('print.order', 'provider_id')

    ink = fields.Selection([('BW', 'Black & White'), ('CL', 'Colour')], "Ink", default='BW')
    paper_weight = fields.Integer("Paper Weight", default=80, readonly=True)
    provider_id = fields.Many2one('print.provider', 'Print Provider', required=True, default=_default_print_provider)
    provider_balance = fields.Float("Provider Credit", digits=(16, 2), related='provider_id.balance')
    provider_environment = fields.Selection([('test', 'Test'), ('production', 'Production')], "Environment", default=False, related='provider_id.environment')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_default_currency)
    print_order_line_wizard_ids = fields.One2many('print.order.line.wizard', 'print_order_wizard_id', string='Lines')

    error_message = fields.Text("Error", compute='_compute_error_message')

    @api.multi
    @api.onchange('provider_id')
    def onchange_print_order_lines(self):
        for wiz in self:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model', False)
            if active_ids and active_model:
                lines = []
                for rec in self.env[active_model].browse(active_ids):
                    lines.append({
                        'res_id': rec.id,
                        'res_model': active_model,
                        'partner_id': rec.partner_id.id,
                        'last_send_date': rec.print_sent_date,
                    })
                wiz.print_order_line_wizard_ids = [(0, 0, vals) for vals in lines]

    @api.one
    @api.depends('print_order_line_wizard_ids')
    def _compute_error_message(self):
        message = False
        unsendable = len(self.print_order_line_wizard_ids.filtered(lambda l: l.state != 'ok'))
        if unsendable:
            if len(self.print_order_line_wizard_ids) == 1:
                current_state = self.print_order_line_wizard_ids[0].state
                state_selection = dict(self.env['print.order.line.wizard']._default_selection_state())
                message = _("The document you want to send contains the following mistake : %s") % (state_selection.get(current_state, "Unknow error."),)
            else:
                message = _("At least one of the document you want to send contains a mistake.")
        self.error_message = message

    @api.multi
    def action_apply(self):
        PrintOrder = self.env['print.order']
        for wizard in self:
            # raise UserError if the provider is not configured
            wizard.provider_id.check_configuration()
            # don't do anything if the balance is too small in the production mode (in test mode, allow all)
            wizard.provider_id.check_credit()
            for line in wizard.print_order_line_wizard_ids:
                PrintOrder.create({
                    'ink' : wizard.ink,
                    'paper_weight' : wizard.paper_weight,
                    'provider_id' : wizard.provider_id.id,
                    'currency_id' : wizard.currency_id.id,
                    'user_id' : self._uid,
                    'res_id' : line.res_id,
                    'res_model' : line.res_model,
                    # duplicate partner infos
                    'partner_id' : line.partner_id.id,
                    'partner_name' : line.partner_id.name,
                    'partner_street' : line.partner_id.street,
                    'partner_street2' : line.partner_id.street2,
                    'partner_state_id' : line.partner_id.state_id.id,
                    'partner_zip' : line.partner_id.zip,
                    'partner_city' : line.partner_id.city,
                    'partner_country_id' : line.partner_id.country_id.id,
                })
        return {'type': 'ir.actions.act_window_close'}



class PrintOrderLineWizard(models.TransientModel):

    _name = 'print.order.line.wizard'
    _rec_name = 'id'

    @api.model
    def _default_selection_state(self):
        return [('ok', 'Ready to be sent'), ('bad_postal_address', 'Wrong Postal Address'), ('account_invoice_wrong_state', 'Wrong Invoice State')]


    print_order_wizard_id = fields.Many2one('print.order.wizard', 'Print Order Wizard')
    res_id = fields.Integer('Resource ID')
    res_model = fields.Char('Resource Model')
    partner_id = fields.Many2one('res.partner', 'Recipient partner')
    last_send_date = fields.Datetime("Last Send Date", default=False)

    state = fields.Selection('_default_selection_state', string='State', compute='_compute_state', store=True)

    @api.one
    @api.depends('partner_id', 'res_model')
    def _compute_state(self):
        state = 'ok'
        if not self.partner_id.has_address:
            state = 'bad_postal_address'
        if self.res_model == 'account.invoice':
            if self.env['account.invoice'].browse(self.res_id).state != 'open':
                state = 'account_invoice_wrong_state'
        self.state = state

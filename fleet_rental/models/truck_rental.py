from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime


class TruckRental(models.Model):
    _name = 'truck.rental'
    _description = 'Truck Rental'

    name = fields.Char("REG. NO.")
    machi = fields.Char("MACHI")
    r_no = fields.Char("R. NO.")
    card_no_fastra = fields.Char("CARD NUMBER ON FASTRA")
    serial_no = fields.Integer("S/N")


class VehicleExpense(models.Model):
    _name = 'vehicle.expense'
    _description = 'Vehicle Expense'
    _rec_name = "truck_rental_id"

    name = fields.Char()
    truck_rental_id = fields.Many2one('truck.rental', string="Truck")
    machi = fields.Char("MACHI", related="truck_rental_id.machi")
    r_no = fields.Char("R. NO.", related="truck_rental_id.r_no")
    card_no_fastra = fields.Char("CARD NUMBER ON FASTRA", related="truck_rental_id.card_no_fastra")
    reg_no = fields.Char("REG. NO.", related="truck_rental_id.name")
    expense_category = fields.Char('Expense Category')
    description = fields.Char("Description")
    amount = fields.Float("Amount")
    date = fields.Date('Date', default=fields.Date.context_today)
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal' )
    move_ids = fields.Many2many('account.move', 'rental_vehicle_expense_rel', 'vehicle_expense_id', 'move_id', string="Moves")
    invoice_count = fields.Integer(compute='_invoice_count', string='# Invoice', copy=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('send_for_approve', 'Send For Approve'),
                              ('approved', 'Approved'),
                              ('disapprove', 'Disapprove')], default='draft')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('vehicle.expense')
        return super(VehicleExpense, self).create(vals)

    @api.multi
    def _invoice_count(self):
        self.invoice_count = len(self.move_ids.ids)

    @api.multi
    def action_invoice_generate(self):
        if not self.journal_id:
            raise UserError(_('Journal is not set!! Please Set Journal.'))
        if not self.account_credit or not self.account_debit:
            raise UserError(_('You need to set debit/credit account for validate.'))

        debit_vals = {
            'name': self.name or '',
            'debit': self.amount,
            'credit': 0.0,
            'account_id': self.account_debit.id,
        }
        credit_vals = {
            'name': self.name or '',
            'debit': 0.0,
            'credit': self.amount,
            'account_id': self.account_credit.id,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': datetime.now().date(),
            'ref': self.name or '',
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.action_post()
        self.write({'move_ids': [(4, move.id)]})
        return

    @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }

    @api.multi
    def action_send_for_approve(self):
        self.write({'state': 'send_for_approve'})

    @api.multi
    def action_approved(self):
        self.write({'state': 'approved'})

    @api.multi
    def action_disapproved(self):
        self.write({'state': 'disapprove'})

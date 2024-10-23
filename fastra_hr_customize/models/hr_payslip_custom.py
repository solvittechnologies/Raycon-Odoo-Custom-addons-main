from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
from io import BytesIO
from odoo.exceptions import UserError

Months = [('January', 'January'),
          ('february', 'February'),
          ('march', 'March'),
          ('april', 'April'),
          ('may', 'May'),
          ('june', 'June'),
          ('july', 'July'),
          ('august', 'August'),
          ('september', 'September'),
          ('october', 'October'),
          ('november', 'November'),
          ('december', 'December')]

Payroll_Type_Selection = [('basic_salary', 'Basic Salary'),
                              ('annual_leave', 'Annual Leave'),
                              ('feeding', 'Feeding'),
                              ('furniture', 'Furniture'),
                              ('housing', 'Housing'),
                              ('medical', "Medical"),
                              ('ordinary_overtime', "Ordinary Over-Time"),
                              ('public_overtime', 'Public Over-Time'),
                              ('sunday_overtime', 'Sunday Over-Time'),
                              ('transport', 'Transport'),
                              ('utility', 'Utility'),
                              ('bonus', 'Bonus'),
                              ('gross', 'Gross'),
                              ('gross_yearly', 'Yearly Gross'),
                              ('pension', 'Pension'),
                              ('other_statutory_deduction', 'Other Statutory Deduction'),
                              ('tax_free_allowance', 'Tax-Free Allowance'),
                              ('consolidated_relief', 'Consolidated Relief (CRA)'),
                              ('consolidated_relief', 'Gross Income Relief'),
                              ('taxable_amount', 'Taxable amount'),
                              ('paye', 'PAYE'),
                              ('net', 'Net'),
                              ('absent_deduction', 'ABSENT DEDUCTION'),
                              ('loan_deduction', 'Loan'),
                              ('payroll_deduction', 'Payroll DEDUCTION'),
                              ('non_taxable_payroll_deduction', 'Non Taxable Payroll DEDUCTION'),
                              ('union_dues', 'Union Dues'),
                              ('pay_amount', 'Pay Amount'),
                              ('leave_grant', 'Leave Grant'),
                              ('payoff', 'Payoff'),
                              ('others', 'Others'),
                              ('iou', 'IOU'),
                              ('other_deduction', 'Other DEDUCTION'),
                              ('milk', 'Milk'),
                              ]

class HRPayslipCustom(models.Model):
    _name = 'hr.payslip.custom'

    name = fields.Char("Payslip Name")
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], string="State", default='draft')
    location_id = fields.Many2one('stock.location', "Location")
    date_from = fields.Date(string='Date From', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            )
    date_to = fields.Date(string='Date To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          )
    month = fields.Selection(Months, string="Month")
    employee_tag = fields.Char("Reference Number")
    account_analytic_id = fields.Many2one('account.analytic.account', "Analytic Account")
    payslip_custom_line_ids = fields.One2many('hr.payslip.custom.line', 'payslip_custom_id', string="Lines", copy = True)

    account_tax_id = fields.Many2one('account.tax', 'Tax')
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal', states={'validated': [('readonly', True)]}, )
    move_ids = fields.Many2many('account.move', 'hr_custom_move_rel', 'hr_custom_id', 'move_id', string="Moves",compute='get_move_ids')
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')
    fastra_hr_payroll_account_line_ids = fields.One2many('fastra.hr.payslip.account.line', 'fastra_payroll_id',string="Account Lines")
    fastra_hr_payroll_individual_account_line_ids = fields.One2many('fastra.hr.payslip.individual.account.line','fastra_payroll_id',string="Individual Account Lines")

    @api.multi
    @api.depends('fastra_hr_payroll_account_line_ids', 'fastra_hr_payroll_individual_account_line_ids')
    def get_move_ids(self):
        for rec in self:
            move_ids_list = []
            for line in rec.fastra_hr_payroll_account_line_ids:
                if line.move_id:
                    move_ids_list.append(line.move_id.id)
            for account_line in rec.fastra_hr_payroll_individual_account_line_ids:
                if account_line.move_id:
                    move_ids_list.append(account_line.move_id.id)
            rec.move_ids = [(6, 0, move_ids_list)]
    @api.multi
    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            self.account_debit = self.location_id.account_debit and self.location_id.account_debit.id or False
            self.account_credit = self.location_id.account_credit and self.location_id.account_credit or False
            self.journal_id = self.location_id.journal_id and self.location_id.journal_id.id or False

    @api.multi
    def action_validate(self):

        self.write({
                    'state': 'validated'})

        vals = {'name': self.name,
                'location_id': self.location_id and self.location_id.id or False,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'month': self.month,
                'employee_tag': self.employee_tag,
                'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False,
                'line_ids': []}
        for line in self.payslip_custom_line_ids:
            vals['line_ids'].append((0, 0, {'beneficiary_name': line.employee_id and line.employee_id.name or False,
                                            'payment_amount': line.pay_amount,
                                            'transaction_reference_number': line.employee_code}))
        self.env['salaries.excel.sheet'].sudo().create(vals)
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

    def generate_excel(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        worksheet = workbook.add_worksheet('Payroll Report')

        bold = workbook.add_format({'bold': True})
        border = workbook.add_format({'border': 1})
        format1 = workbook.add_format({'bold': True, 'border': 1})

        row = 0
        worksheet.write(row, 0, 'Employee', format1)
        worksheet.write(row, 1, 'Employee ID', format1)
        worksheet.write(row, 2, 'Working Hours', format1)
        worksheet.write(row, 3, 'OT Hours', format1)
        worksheet.write(row, 4, 'SUN OT Hours', format1)
        worksheet.write(row, 5, 'PUB OT Hours', format1)
        worksheet.write(row, 6, 'Basic Salary', format1)
        worksheet.write(row, 7, 'Annual Leave', format1)
        worksheet.write(row, 8, 'Feeding', format1)
        worksheet.write(row, 9, 'Furniture', format1)
        worksheet.write(row, 10, 'Housing', format1)
        worksheet.write(row, 11, 'Medical', format1)
        worksheet.write(row, 12, 'Ordinary Over-Time', format1)
        worksheet.write(row, 13, 'Public Over-Time', format1)
        worksheet.write(row, 14, 'Sunday Over-Time', format1)
        worksheet.write(row, 15, 'Transport', format1)
        worksheet.write(row, 16, 'Utility', format1)
        worksheet.write(row, 17, 'Bonus', format1)
        worksheet.write(row, 18, 'Gross', format1)
        worksheet.write(row, 19, 'Yearly Gross', format1)
        worksheet.write(row, 20, 'Pension', format1)
        worksheet.write(row, 21, 'Other Statutory Deduction', format1)
        worksheet.write(row, 22, 'Tax-Free Allowance', format1)
        worksheet.write(row, 23, 'Consolidated Relief (CRA)', format1)
        worksheet.write(row, 24, 'Gross Income Relief', format1)
        worksheet.write(row, 25, 'Taxable amount', format1)
        worksheet.write(row, 26, 'PAYE', format1)
        worksheet.write(row, 27, 'Net', format1)
        worksheet.write(row, 28, 'ABSENT DEDUCTION', format1)
        worksheet.write(row, 29, 'Loan', format1)
        worksheet.write(row, 30, 'Payroll DEDUCTION', format1)
        worksheet.write(row, 31, 'Non Taxable Payroll DEDUCTION', format1)
        worksheet.write(row, 32, 'Union Dues', format1)
        worksheet.write(row, 33, 'Pay Amount', format1)

        row += 1
        working_hours = ot_hours = sun_ot_hours = pub_ot_hours = basic_salary = annual_leave = feeding = furniture = housing = medical = ordinary_overtime = public_overtime = sunday_overtime = transport = utility = bonus = gross = gross_yearly = pension = other_statutory_deduction = tax_free_allowance = consolidated_relief = gross_income_relief = taxable_amount = paye = net = absent_deduction = loan_deduction = payroll_deduction = non_taxable_payroll_deduction = union_dues = pay_amount = 0.0
        for line in self.payslip_custom_line_ids:
            worksheet.write(row, 0, line.employee_id and line.employee_id.name or '')
            worksheet.write(row, 1, line.employee_code or '')
            worksheet.write(row, 2, line.working_hours or '')
            working_hours += line.working_hours
            worksheet.write(row, 3, line.ot_hours or '')
            ot_hours += line.ot_hours
            worksheet.write(row, 4, line.sun_ot_hours or '')
            sun_ot_hours += line.sun_ot_hours
            worksheet.write(row, 5, line.pub_ot_hours or '')
            pub_ot_hours += line.pub_ot_hours
            worksheet.write(row, 6, line.basic_salary or '')
            basic_salary += line.basic_salary
            worksheet.write(row, 7, line.annual_leave or '')
            annual_leave += line.annual_leave
            worksheet.write(row, 8, line.feeding or '')
            feeding += line.feeding
            worksheet.write(row, 9, line.furniture or '')
            furniture += line.furniture
            worksheet.write(row, 10, line.housing or '')
            housing += line.housing
            worksheet.write(row, 11, line.medical or '')
            medical += line.medical
            worksheet.write(row, 12, line.ordinary_overtime or '')
            ordinary_overtime += line.ordinary_overtime
            worksheet.write(row, 13, line.public_overtime or '')
            public_overtime += line.public_overtime
            worksheet.write(row, 14, line.sunday_overtime or '')
            sunday_overtime += line.sunday_overtime
            worksheet.write(row, 15, line.transport or '')
            transport += line.transport
            worksheet.write(row, 16, line.utility or '')
            utility += line.utility
            worksheet.write(row, 17, line.bonus or '')
            bonus += line.bonus
            worksheet.write(row, 18, line.gross or '')
            gross += line.gross
            worksheet.write(row, 19, line.gross_yearly or '')
            gross_yearly += line.gross_yearly
            worksheet.write(row, 20, line.pension or '')
            pension += line.pension
            worksheet.write(row, 21, line.other_statutory_deduction or '')
            other_statutory_deduction += line.other_statutory_deduction
            worksheet.write(row, 22, line.tax_free_allowance or '')
            tax_free_allowance += line.tax_free_allowance
            worksheet.write(row, 23, line.consolidated_relief or '')
            consolidated_relief += line.consolidated_relief
            worksheet.write(row, 24, line.gross_income_relief or '')
            gross_income_relief += line.gross_income_relief
            worksheet.write(row, 25, line.taxable_amount or '')
            taxable_amount += line.taxable_amount
            worksheet.write(row, 26, line.paye or '')
            paye += line.paye
            worksheet.write(row, 27, line.net or '')
            net += line.net
            worksheet.write(row, 28, line.absent_deduction or '')
            absent_deduction += line.absent_deduction
            worksheet.write(row, 29, line.loan_deduction or '')
            loan_deduction += line.loan_deduction
            worksheet.write(row, 30, line.payroll_deduction or '')
            payroll_deduction += line.payroll_deduction
            worksheet.write(row, 31, line.non_taxable_payroll_deduction or '')
            non_taxable_payroll_deduction += line.non_taxable_payroll_deduction
            worksheet.write(row, 32, line.union_dues or '')
            union_dues += line.union_dues
            worksheet.write(row, 33, line.pay_amount or '')
            pay_amount += line.pay_amount
            row += 1

        worksheet.write(row, 1, 'Total', bold)
        worksheet.write(row, 2, working_hours, bold)
        worksheet.write(row, 3, ot_hours, bold)
        worksheet.write(row, 4, sun_ot_hours, bold)
        worksheet.write(row, 5, pub_ot_hours, bold)
        worksheet.write(row, 6, basic_salary, bold)
        worksheet.write(row, 7, annual_leave, bold)
        worksheet.write(row, 8, feeding, bold)
        worksheet.write(row, 9, furniture, bold)
        worksheet.write(row, 10, housing, bold)
        worksheet.write(row, 11, medical, bold)
        worksheet.write(row, 12, ordinary_overtime, bold)
        worksheet.write(row, 13, public_overtime, bold)
        worksheet.write(row, 14, sunday_overtime, bold)
        worksheet.write(row, 15, transport, bold)
        worksheet.write(row, 16, utility, bold)
        worksheet.write(row, 17, bonus, bold)
        worksheet.write(row, 18, gross, bold)
        worksheet.write(row, 19, gross_yearly, bold)
        worksheet.write(row, 20, pension, bold)
        worksheet.write(row, 21, other_statutory_deduction, bold)
        worksheet.write(row, 22, tax_free_allowance, bold)
        worksheet.write(row, 23, consolidated_relief, bold)
        worksheet.write(row, 24, gross_income_relief, bold)
        worksheet.write(row, 25, taxable_amount, bold)
        worksheet.write(row, 26, paye, bold)
        worksheet.write(row, 27, net, bold)
        worksheet.write(row, 28, absent_deduction, bold)
        worksheet.write(row, 29, loan_deduction, bold)
        worksheet.write(row, 30, payroll_deduction, bold)
        worksheet.write(row, 31, non_taxable_payroll_deduction, bold)
        worksheet.write(row, 32, union_dues, bold)
        worksheet.write(row, 33, pay_amount, bold)

        workbook.close()
        file_data.seek(0)
        self.write(
            {'excel_file': base64.encodebytes(file_data.read()),
             'file_name': '%s.xlsx' % self.name})

        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=hr.payslip.custom&id=" + str(self.id) + "&filename_field=filename&field=excel_file&download=true&filename=" + self.file_name,
            'target': 'current'
        }

    @api.model
    def create(self, values):
        if not values.get('employee_tag', False):
            reference_code = self.env['ir.sequence'].next_by_code('employee.payroll.reference')
            values['employee_tag'] = reference_code[:-1]
        return super(HRPayslipCustom, self).create(values)


class HRPayslipCustomLine(models.Model):
    _name = 'hr.payslip.custom.line'

    payslip_custom_id = fields.Many2one('hr.payslip.custom', "Payslip")
    employee_id = fields.Many2one('hr.employee', string="Employee",copy = True)
    employee_code = fields.Char('Employee ID')
    working_hours = fields.Float('Working Hours')
    ot_hours = fields.Float("OT Hours")
    sun_ot_hours = fields.Float("SUN OT Hours")
    pub_ot_hours = fields.Float("PUB OT Hours")
    basic_salary = fields.Float('Basic Salary')
    annual_leave = fields.Float('Annual Leave')
    feeding = fields.Float('Feeding')
    furniture = fields.Float('Furniture')
    housing = fields.Float('Housing')
    medical = fields.Float('Medical')
    ordinary_overtime = fields.Float('Ordinary Over-Time')
    public_overtime = fields.Float('Public Over-Time')
    sunday_overtime = fields.Float('Sunday Over-Time')
    transport = fields.Float('Transport')
    utility = fields.Float('Utility')
    bonus = fields.Float('Bonus')
    gross = fields.Float('Gross')
    gross_yearly = fields.Float('Yearly Gross', compute='get_yearly_gross')
    pension = fields.Float('Pension')
    other_statutory_deduction = fields.Float('Other Statutory Deduction')
    tax_free_allowance = fields.Float('Tax-Free Allowance')
    consolidated_relief = fields.Float('Consolidated Relief (CRA)', default=200000)
    gross_income_relief = fields.Float('Gross Income Relief')
    taxable_amount = fields.Float('Taxable amount')
    paye = fields.Float('PAYE')
    net = fields.Float('Net')
    absent_deduction = fields.Float('ABSENT DEDUCTION')
    loan_deduction = fields.Float('Loan')
    payroll_deduction = fields.Float('Payroll DEDUCTION')
    non_taxable_payroll_deduction = fields.Float('Non Taxable Payroll DEDUCTION')
    union_dues = fields.Float('Union Dues')
    pay_amount = fields.Float('Pay Amount')

    leave_grant = fields.Float('Leave Grant')
    payoff = fields.Float('Payoff')
    others = fields.Float('Others')
    iou = fields.Float('IOU')
    other_deduction = fields.Float('Other DEDUCTION')
    milk = fields.Float('Milk')

    @api.model
    def create(self, values):
        if not values.get('employee_code', False):
            values['employee_code'] = self.env['ir.sequence'].next_by_code('employee.payroll.code')
        return super(HRPayslipCustomLine, self).create(values)

    @api.multi
    @api.onchange('gross', 'consolidated_relief', 'gross_income_relief', 'pension')
    def onchange_paye_amount(self):
        paye = 0.0
        cra = self.consolidated_relief
        gross_salary_year = self.gross * 12
        if gross_salary_year < 300000:
            paye = (gross_salary_year * 1) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        gross_income_relief = (gross_salary_year * 20) / 100
        taxable_amount = gross_salary_year - (cra + gross_income_relief) - self.pension
        if taxable_amount > 3200000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            paye += (500000 * 19) / 100
            paye += (1600000 * 21) / 100
            taxable_amount -= 3200000
            paye += (taxable_amount * 24) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 1600000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            paye += (500000 * 19) / 100
            taxable_amount -= 1600000
            paye += (taxable_amount * 21) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 1100000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            paye += (500000 * 15) / 100
            taxable_amount -= 1100000
            paye += (taxable_amount * 19) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 600000:
            paye += (300000 * 7) / 100
            paye += (300000 * 11) / 100
            taxable_amount -= 600000
            paye += (taxable_amount * 15) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        elif taxable_amount > 300000:
            paye += (300000 * 7) / 100
            taxable_amount -= 300000
            paye += (taxable_amount * 11) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return
        else:
            paye += (taxable_amount * 7) / 100
            self.update({'paye': float(round(paye / 12, 2))})
            return

    @api.multi
    @api.onchange('basic_salary', 'annual_leave', 'feeding', 'furniture', 'housing', 'medical',
                  'ordinary_overtime', 'public_overtime', 'sunday_overtime', 'transport', 'utility', 'bonus')
    def get_gross_amount(self):
        for rec in self:
            rec.gross = rec.basic_salary + rec.annual_leave + rec.feeding + rec.furniture + rec.housing + rec.medical + rec.ordinary_overtime + rec.public_overtime + rec.sunday_overtime + rec.transport + rec.utility + rec.bonus

    @api.multi
    @api.depends('gross')
    def get_yearly_gross(self):
        for rec in self:
            rec.gross_yearly = rec.gross * 12

    @api.multi
    @api.onchange('gross_yearly')
    def get_gross_income_relief(self):
        for rec in self:
            rec.gross_income_relief = (rec.gross_yearly * 20) / 100

    @api.multi
    @api.onchange('gross_yearly', 'pension', 'other_statutory_deduction',
                  'tax_free_allowance', 'consolidated_relief', 'gross_income_relief')
    def get_taxable_amount(self):
        for rec in self:
            if rec.gross_yearly > 300000:
                rec.taxable_amount = rec.gross_yearly - (rec.consolidated_relief + rec.gross_income_relief) - rec.pension
            else:
                rec.taxable_amount = 0.0

    @api.multi
    @api.onchange('paye', 'gross')
    def get_net(self):
        for rec in self:
            rec.net = rec.gross - rec.paye

    @api.multi
    @api.onchange('union_dues', 'net', 'absent_deduction', 'loan_deduction', 'payroll_deduction',
                  'non_taxable_payroll_deduction')
    def get_pay_amount(self):
        for rec in self:
            rec.pay_amount = rec.net - rec.absent_deduction - rec.loan_deduction - rec.payroll_deduction - rec.non_taxable_payroll_deduction - rec.union_dues


class FastraHrPayslipAccountLine(models.Model):
    _name = 'fastra.hr.payslip.account.line'

    fastra_payroll_id = fields.Many2one('hr.payslip.custom', string="Payroll")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    payroll_type = fields.Selection(selection=Payroll_Type_Selection, string="Payroll Type")
    type_amount = fields.Float('Type Amount', compute='get_type_amount')
    line_ids = fields.Many2many('hr.payslip.custom.line', compute='get_line_ids')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Post')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")

    @api.model
    def create(self, vals):
        res = super(FastraHrPayslipAccountLine, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': res.type_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': 0.0,
                'credit': res.type_amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(FastraHrPayslipAccountLine, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res


    @api.multi
    @api.depends('fastra_payroll_id', 'fastra_payroll_id.payslip_custom_line_ids')
    def get_line_ids(self):
        for rec in self:
            if rec.fastra_payroll_id and rec.fastra_payroll_id.payslip_custom_line_ids:
                rec.line_ids = [(6, 0, rec.fastra_payroll_id.payslip_custom_line_ids.ids)]
            else:
                rec.line_ids = [(6, 0, [])]

    @api.multi
    @api.depends('payroll_type', 'line_ids')
    def get_type_amount(self):
        for rec in self:
            rec.type_amount = 0.0
            if rec.payroll_type == 'basic_salary':
                rec.type_amount = sum(rec.line_ids.mapped('basic_salary'))

            if rec.payroll_type == 'annual_leave':
                rec.type_amount = sum(rec.line_ids.mapped('annual_leave'))

            if rec.payroll_type == 'feeding':
                rec.type_amount = sum(rec.line_ids.mapped('feeding'))

            if rec.payroll_type == 'furniture':
                rec.type_amount = sum(rec.line_ids.mapped('furniture'))

            if rec.payroll_type == 'housing':
                rec.type_amount = sum(rec.line_ids.mapped('housing'))

            if rec.payroll_type == 'medical':
                rec.type_amount = sum(rec.line_ids.mapped('medical'))

            if rec.payroll_type == 'ordinary_overtime':
                rec.type_amount = sum(rec.line_ids.mapped('ordinary_overtime'))

            if rec.payroll_type == 'public_overtime':
                rec.type_amount = sum(rec.line_ids.mapped('public_overtime'))

            if rec.payroll_type == 'sunday_overtime':
                rec.type_amount = sum(rec.line_ids.mapped('sunday_overtime'))

            if rec.payroll_type == 'transport':
                rec.type_amount = sum(rec.line_ids.mapped('transport'))

            if rec.payroll_type == 'utility':
                rec.type_amount = sum(rec.line_ids.mapped('utility'))

            if rec.payroll_type == 'bonus':
                rec.type_amount = sum(rec.line_ids.mapped('bonus'))

            if rec.payroll_type == 'gross':
                rec.type_amount = sum(rec.line_ids.mapped('gross'))

            if rec.payroll_type == 'gross_yearly':rec.type_amount = sum(rec.line_ids.mapped('gross_yearly'))

            if rec.payroll_type == 'pension':
                rec.type_amount = sum(rec.line_ids.mapped('pension'))

            if rec.payroll_type == 'other_statutory_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('other_statutory_deduction'))

            if rec.payroll_type == 'tax_free_allowance':
                rec.type_amount = sum(rec.line_ids.mapped('tax_free_allowance'))

            if rec.payroll_type == 'consolidated_relief':
                rec.type_amount = sum(rec.line_ids.mapped('consolidated_relief'))

            if rec.payroll_type == 'consolidated_relief':
                rec.type_amount = sum(rec.line_ids.mapped('consolidated_relief'))

            if rec.payroll_type == 'taxable_amount':
                rec.type_amount = sum(rec.line_ids.mapped('taxable_amount'))

            if rec.payroll_type == 'paye':
                rec.type_amount = sum(rec.line_ids.mapped('paye'))

            if rec.payroll_type == 'net':
                rec.type_amount = sum(rec.line_ids.mapped('net'))

            if rec.payroll_type == 'absent_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('absent_deduction'))

            if rec.payroll_type == 'loan_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('loan_deduction'))

            if rec.payroll_type == 'payroll_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('payroll_deduction'))

            if rec.payroll_type == 'non_taxable_payroll_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('non_taxable_payroll_deduction'))

            if rec.payroll_type == 'union_dues':
                rec.type_amount = sum(rec.line_ids.mapped('union_dues'))

            if rec.payroll_type == 'pay_amount':
                rec.type_amount = sum(rec.line_ids.mapped('pay_amount'))

            if rec.payroll_type == 'leave_grant':
                rec.type_amount = sum(rec.line_ids.mapped('leave_grant'))

            if rec.payroll_type == 'payoff':
                rec.type_amount = sum(rec.line_ids.mapped('payoff'))

            if rec.payroll_type == 'others':
                rec.type_amount = sum(rec.line_ids.mapped('others'))

            if rec.payroll_type == 'iou':
                rec.type_amount = sum(rec.line_ids.mapped('iou'))

            if rec.payroll_type == 'other_deduction':
                rec.type_amount = sum(rec.line_ids.mapped('other_deduction'))

            if rec.payroll_type == 'milk':
                rec.type_amount = sum(rec.line_ids.mapped('milk'))




class IndividualAccountLine(models.Model):
    _name = 'fastra.hr.payslip.individual.account.line'

    employee_id = fields.Many2one('hr.employee', string="Employee Name")
    fastra_payroll_id = fields.Many2one('hr.payslip.custom', string="Payroll")
    account_debit = fields.Many2one('account.account', 'Debit Account', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Credit Account', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal')
    payroll_type = fields.Selection(selection=Payroll_Type_Selection, string="Payroll Type")
    type_amount = fields.Float('Type Amount', compute='get_type_amount')
    line_ids = fields.Many2many('hr.payslip.custom.line', compute='get_line_ids')
    state = fields.Selection([('draft', 'Draft'),
                              ('post', 'Post')], string="Status")
    move_id = fields.Many2one('account.move', string="Move")


    @api.model
    def create(self, vals):
        res = super(IndividualAccountLine, self).create(vals)
        if res and res.state == 'post':
            if not res.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not res.account_credit or not res.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': res.type_amount,
                'credit': 0.0,
                'account_id': res.account_debit.id,
            }
            credit_vals = {
                'name': dict(res._fields['payroll_type'].selection).get(res.payroll_type),
                'debit': 0.0,
                'credit': res.type_amount,
                'account_id': res.account_credit.id,
            }
            vals = {
                'journal_id': res.journal_id.id,
                'date': datetime.now().date(),
                'ref': res.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            res.write({'move_id': move.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(IndividualAccountLine, self).write(vals)
        if vals.get('state', False) and vals['state'] == 'post' and not self.move_id:
            if not self.journal_id:
                raise UserError(_('Journal is not set!! Please Set Journal.'))
            if not self.account_credit or not self.account_debit:
                raise UserError(_('You need to set debit/credit account for validate.'))

            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.now().date(),
                'ref': self.fastra_payroll_id.name,
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'move_id': move.id})
        if vals.get('state', False) and vals['state'] == 'post' and self.move_id:
            self.move_id.button_cancel()
            self.move_id.line_ids.unlink()
            debit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': self.type_amount,
                'credit': 0.0,
                'account_id': self.account_debit.id,
            }
            credit_vals = {
                'name': dict(self._fields['payroll_type'].selection).get(self.payroll_type),
                'debit': 0.0,
                'credit': self.type_amount,
                'account_id': self.account_credit.id,
            }
            self.move_id.write({'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]})
            self.move_id.action_post()
        return res

    @api.multi
    @api.depends('fastra_payroll_id', 'fastra_payroll_id.payslip_custom_line_ids')
    def get_line_ids(self):
        for rec in self:
            if rec.fastra_payroll_id and rec.fastra_payroll_id.payslip_custom_line_ids:
                rec.line_ids = [(6, 0, rec.fastra_payroll_id.payslip_custom_line_ids.ids)]
            else:
                rec.line_ids = [(6, 0, [])]

    @api.multi
    @api.depends('payroll_type', 'line_ids', 'employee_id')
    def get_type_amount(self):
        for rec in self:
            rec.type_amount = 0.0
            if rec.payroll_type == 'basic_salary':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('basic_salary'))

            if rec.payroll_type == 'annual_leave':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('annual_leave'))

            if rec.payroll_type == 'feeding':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'feeding'))

            if rec.payroll_type == 'furniture':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('furniture'))

            if rec.payroll_type == 'housing':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('housing'))

            if rec.payroll_type == 'medical':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('medical'))

            if rec.payroll_type == 'ordinary_overtime':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('ordinary_overtime'))

            if rec.payroll_type == 'public_overtime':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('public_overtime'))

            if rec.payroll_type == 'sunday_overtime':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('sunday_overtime'))

            if rec.payroll_type == 'transport':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('transport'))

            if rec.payroll_type == 'utility':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('utility'))

            if rec.payroll_type == 'bonus':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('bonus'))

            if rec.payroll_type == 'gross':
                rec.type_amount = sum(
                    rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped('gross'))

            if rec.payroll_type == 'gross_yearly':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'gross_yearly'))

            if rec.payroll_type == 'pension':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'pension'))

            if rec.payroll_type == 'other_statutory_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'other_statutory_deduction'))

            if rec.payroll_type == 'tax_free_allowance':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'tax_free_allowance'))

            if rec.payroll_type == 'consolidated_relief':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'consolidated_relief'))

            if rec.payroll_type == 'consolidated_relief':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'consolidated_relief'))

            if rec.payroll_type == 'taxable_amount':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'taxable_amount'))

            if rec.payroll_type == 'paye':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'paye'))

            if rec.payroll_type == 'net':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'net'))

            if rec.payroll_type == 'absent_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'absent_deduction'))

            if rec.payroll_type == 'loan_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'loan_deduction'))

            if rec.payroll_type == 'payroll_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'payroll_deduction'))

            if rec.payroll_type == 'non_taxable_payroll_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'non_taxable_payroll_deduction'))

            if rec.payroll_type == 'union_dues':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'union_dues'))

            if rec.payroll_type == 'pay_amount':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'pay_amount'))

            if rec.payroll_type == 'leave_grant':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'leave_grant'))

            if rec.payroll_type == 'payoff':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'payoff'))

            if rec.payroll_type == 'others':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'others'))

            if rec.payroll_type == 'iou':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'iou'))

            if rec.payroll_type == 'other_deduction':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'other_deduction'))

            if rec.payroll_type == 'milk':
                rec.type_amount = sum(rec.line_ids.filtered(lambda l: l.employee_id.id == rec.employee_id.id).mapped(
                    'milk'))



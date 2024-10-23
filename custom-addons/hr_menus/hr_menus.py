from odoo import models, fields,api, _
import time
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    def _get_current_user_id(self):
        user = self.env.user.id

        if user == self.user_id.id:
            self.user_uid = True
        else:
            self.user_uid = False

    Title = fields.Char(string='Title')
    Position = fields.Char(string='Position Employed For')
    Year = fields.Char(string='Employment Year')
    Lga = fields.Char(string='LGA')
    State_Origin = fields.Char(string='State of Origin')

    email = fields.Char(string='Email Address')
    phone_no = fields.Char(string='Phone Number')
    postal_address = fields.Char(string='Postal Address')
    business_no = fields.Char(string='Business Telephone Number')
    tax_id = fields.Char(string='Tax ID')
    nhf_no = fields.Char(string='NHF_Number')

    reference_name = fields.Char("Name")
    reference_address = fields.Char("Address")
    reference_email = fields.Char("Email")
    reference_phone_number = fields.Char("Phone Number")
    reference_occupation = fields.Char("Occupation")
    reference_employer_details = fields.Char("Employer's Detail")
    relationship_duration_with_reference = fields.Char("Relationship Duration")
    reference_is_guarantor = fields.Boolean()
    guarantor = fields.One2many('hr.inherit_tree', 'form_inherit')

    states_lived_in = fields.Char("States You Have Lived in")
    languages = fields.Char('Language(s)')
    will_to_serve = fields.Boolean("Are you willing to serve in any part of Nigeria?")
    reason_for_not_serving_in_Nigeria = fields.Text("If NO, Give reasons")

    employee_professional_membership = fields.One2many('professional_training.inherit', 'employee_id', string="Employee Professional Membership")
    number_of_companies_employee_worked = fields.Integer("Number of Companies Employee Worked")
    employee_working_experience = fields.One2many('employee.working.experience', 'employee_id')
    employee_current_renumeration = fields.One2many('renumeration.breakdown.list', 'employee_id')
    employee_medical_history = fields.One2many('medical.history', 'employee_id')
    employee_likes_dislikes = fields.One2many('likes.dislikes', 'employee_id')
    employee_hobbies_socials = fields.One2many('hobbies.socials', 'employee_id')
    user_uid = fields.Boolean(compute="_get_current_user_id")


class HrEmployeeInheritTree(models.Model):
    _name = 'hr.inherit_tree'

    form_inherit = fields.Many2one('hr.employee', readonly=True)
    guarantor_name = fields.Char("Name")
    guarantor_address = fields.Char("Address")
    guarantor_occupation = fields.Char("Occupation")
    guarantor_employer_details = fields.Char("Employer's Detail")
    relationship_duration_with_guarantor = fields.Char("Relationship Duration")

class ProfessionalMembershipInherit(models.Model):
    _name = 'professional_training.inherit'

    employee_id = fields.Many2one('hr.employee',string="Related Employee")
    professional_membership = fields.Char("Professional Membership/Trainings")
    date = fields.Date("Date")

class WorkingExperienceRecord(models.Model):
    _name = 'employee.working.experience'

    from_year= fields.Date(string="From")
    to_year=fields.Date(string="To")
    name_of_employer = fields.Char("Name of Employer")
    address_of_employer = fields.Text("Employer's Address")
    employer_email=fields.Char("Employer's Email Address")
    position_held= fields.Char("Position Held")
    job_description=fields.Text("Job Description")
    total_renumeration_per_annum =fields.Float("Total Renumeration per Annum")
    reason_for_leaving = fields.Text("Reasons for Leaving")
    employee_id = fields.Many2one('hr.employee',string="Related Employee")

class RenumerationList(models.Model):
    _name = 'renumeration.breakdown.list'

    employee_id = fields.Many2one('hr.employee',string="Related Employee")
    item = fields.Char(string="Item")
    amount = fields.Float(string="Amount")

class MedicalHistory(models.Model):
    _name = 'medical.history'

    employee_id = fields.Many2one('hr.employee',string="Related Employee")
    any_dissability = fields.Selection([('yes','Yes'),('no','No')], string="Have you any disability?")
    serious_illness = fields.Selection([('yes','Yes'),('no','No')], string="Are you suffering from any serious illnesses?")
    type_of_serious_illness = fields.Char("What type of ailment")
    recurrent_illness = fields.Selection([('yes','Yes'),('no','No')], string="Are you suffering from any recurrent illness?")
    type_of_recurrent_illness = fields.Char("What type of ailment")
    undergo_medical_test = fields.Selection([('yes','Yes'),('no','No')], string="Are you prepared to undergo medical test?")

class HobbiesAndSocials(models.Model):
    _name = 'hobbies.socials'

    hobbies = fields.Char("Hobbies")
    socials = fields.Char("Socials")
    employee_id = fields.Many2one('hr.employee', string="Related Employee")

class LikesAndDislikes(models.Model):
    _name = 'likes.dislikes'

    likes = fields.Char("Likes")
    dislikes = fields.Char("Dislikes")
    employee_id = fields.Many2one('hr.employee', string="Related Employee")



class HRPayslipExtend(models.Model):
    _inherit = "hr.payslip"


    def action_send_email_payslip(self):
        print('sending email')
        template_id = self.env.ref('hr_menus.email_template_hr_payslip_temp').id
        self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

    """@api.onchange('struct_id')
    def compute_input_lines(self):
        for rec in self:
            input_lines = []
            if rec.struct_id:
                for rule in rec.struct_id.rule_ids:
                    for input in rule.input_ids:
                        #print(input)
                        input_lines.append((0,0,
			    {
			      'name':input.name,
                              'code':input.code,
                              'contract_id':rec.contract_id.id if rec.contract_id else None
			    }))
            rec.input_line_ids = input_lines"""

    user_id = fields.Many2one('res.users', string='Current User', track_visibility='onchange',readonly=True, states={'draft': [('readonly', False)]},default=lambda self: self.env.user, copy=False)

class HrExpenseInherit(models.Model):
    _inherit = 'hr.expense'


#    def action_notify(self):
#        for rec in self:
#            users = self.env.ref('hr.group_hr_manager').users
#            for user in users:
#                rec.user.notify_info(message='New staff request submitted')


#    @api.multi
    def action_notify(self):
        for rec in self:
#            rec.state = 'reported'
            users = self.env.ref('hr.group_hr_manager').users
            for user in users:
                print(user.partner_id.name)
                rec.message_post(body="A staff request is awaiting approval",partner_ids=[user.partner_id.id],message_type= "notification",subtype_id=  self.env.ref("mail.mt_comment").id,subject=_("Staff Request Awaiting Approval"),model=self._name,res_id= rec.id)


class HrPayslipRunInherit(models.Model):
    _inherit = 'hr.payslip.run'

    def action_send_email_payslip(self):
        for rec in self.slip_ids:
            print('sending email')
            template_id = rec.env.ref('hr_menus.email_template_hr_payslip_temp').id
            rec.env['mail.template'].browse(template_id).send_mail(rec.id, force_send=True)


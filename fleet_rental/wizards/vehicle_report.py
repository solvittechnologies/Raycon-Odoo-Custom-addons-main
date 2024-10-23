from odoo import fields, models, api
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
from io import BytesIO
from datetime import datetime


class VehicleReport(models.TransientModel):
    _name = 'vehicle.report'
    _description = 'Vehicle Report'

    truck_rental_id = fields.Many2one('truck.rental', string="Truck")
    rent_start_date = fields.Date("Rent Start Date")
    rent_end_date = fields.Date("Rent End Date")
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')

    def action_pdf(self):
        return self.env.ref('fleet_rental.report_vehicle_expense').report_action(self)

    def get_vehicle_expense(self):
        vehicle_expense_ids = self.env['vehicle.expense'].search([('truck_rental_id', '=', self.truck_rental_id.id),
                                                                  ('date', '>=', self.rent_start_date),
                                                                  ('date', '<=', self.rent_end_date)])
        total_truck_cost = 0.0
        for vehicle_expense_id in vehicle_expense_ids:
            total_truck_cost += vehicle_expense_id.amount
        return total_truck_cost

    def get_vehicle_income(self):
        checklist_ids = self.env['car.rental.checklist'].search([('truck_rental_id', '=', self.truck_rental_id.id)])
        total_truck_income = 0.0
        for checklist_id in checklist_ids:
            total_truck_income += checklist_id.price
        return  total_truck_income

    def action_xlsx(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)

        sheet = workbook.add_worksheet('RENTAL VEHICLE Report')

        format1 = workbook.add_format({'bold': True, 'border': 1})
        border = workbook.add_format({'bold': True, 'border': 1})

        row = 0
        sheet.merge_range(row, 0, row, 6, 'RENTAL VEHICLE Report', border)
        row = 2
        sheet.write(row, 0, 'Date', format1)
        sheet.write(row, 1,
                        self.rent_start_date.strftime("%d-%m-%Y") + ' to ' + self.rent_end_date.strftime("%d-%m-%Y"))
        sheet.merge_range(row, 4, row, 6, 'Profit/Loss', format1)

        row += 1
        sheet.write(row, 0, 'MACHI', format1)
        sheet.write(row, 1, 'R. NO.', format1)
        sheet.write(row, 2, 'REG.NO.', format1)
        sheet.write(row, 3, 'CARD NUMBER ', format1)
        sheet.write(row, 4, 'Cost', format1)
        sheet.write(row, 5, 'Income', format1)
        sheet.write(row, 6, 'Net Difference', format1)

        total_truck_cost = self.get_vehicle_expense()
        total_truck_income = self.get_vehicle_income()

        row += 1
        sheet.write(row, 0, self.truck_rental_id.machi or '')
        sheet.write(row, 1, self.truck_rental_id.r_no or '')
        sheet.write(row, 2, self.truck_rental_id.name or '')
        sheet.write(row, 3, self.truck_rental_id.card_no_fastra or '')
        sheet.write(row, 4, total_truck_cost or '')
        sheet.write(row, 5, total_truck_income or '')
        sheet.write(row, 6, total_truck_income - total_truck_cost or '')

        row += 1
        sheet.write(row, 3, 'Totals', format1)
        sheet.write(row, 4, total_truck_cost or '', format1)
        sheet.write(row, 5, total_truck_income or '', format1)
        sheet.write(row, 6, total_truck_income - total_truck_cost or '', format1)

        workbook.close()
        file_data.seek(0)
        self.write(
            {'excel_file': base64.encodebytes(file_data.read()),
             'file_name': 'Vehicle Rental Report.xlsx'})
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=vehicle.report&field=%s&filename_field=%s&id=%s' % (
            'excel_file', 'file_name', self.id),
            'target': 'current'
        }

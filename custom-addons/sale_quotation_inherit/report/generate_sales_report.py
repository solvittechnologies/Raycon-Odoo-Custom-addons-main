from odoo import models
from datetime import datetime, timedelta


class SalesXlsx(models.AbstractModel):
    _name = 'report.crm.general_sales_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet("Sales Report")
        bold = workbook.add_format({'bold': True})
        sheet.set_column(0, 0, 10)
        sheet.set_column(0, 1, 25)
        sheet.set_column(0, 2, 25)
        sheet.set_column(0, 3, 25)
        sheet.set_column(0, 4, 25)
        sheet.set_column(0, 5, 25)
        sheet.set_column(0, 6, 25)
        sheet.write(0, 0, 'S/N', bold)
        sheet.write(0, 1, 'Prospect & Customer (Name of Account/ Location Address/ Name of contact '
                          'Person/ Phone Number/ Designation/ Email.', bold)
        sheet.write(0, 2, 'Proposed Solution', bold)
        sheet.write(0, 3, 'Actions Taken (Summary)', bold)
        sheet.write(0, 4, 'Complaints/ Escalations/ Issues', bold)
        sheet.write(0, 5, 'Probability of Closing Deal %', bold)
        sheet.write(0, 6, 'Amount Quoted (Naira)', bold)

        r = 1
        for obj in lines:
            c = 1
#            print(obj.activities.subject)
            # report_name = obj.name
            # # One sheet by partner
            # sheet = workbook.add_worksheet(report_name[:31])
            # bold = workbook.add_format({'bold': True})

            sheet.write(r, 0, r)
            if obj.partner_id:
                sheet.write(r, c, obj.partner_id.name)
            c += 1
            if obj.name:
                sheet.write(r, c, obj.name)
            c += 1
            for act in obj.activities:
                sheet.write(r, c, act.subject)
            c += 1
            if obj.complaints:
                sheet.write(r, c, obj.complaints)
            c += 1
            sheet.write(r, c, obj.probability)
            c += 1
            sheet.write(r, c, obj.planned_revenue)
            c += 1
            r += 1



class QuotationXlsx(models.AbstractModel):
    _name = 'report.sale.quotation_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet("Sales Report")
        bold = workbook.add_format({'bold': True})

        sheet.set_column(0, 0, 25)
        sheet.set_column(0, 1, 25)
        sheet.set_column(0, 2, 25)
        sheet.set_column(0, 3, 25)
        sheet.set_column(0, 4, 25)
        sheet.set_column(0, 5, 25)
        sheet.set_column(0, 6, 25)
        sheet.set_column(0, 7, 25)
#        sheet.set_column(0, 8, 25)
#        sheet.set_column(0, 9, 25)
#        sheet.set_column(0, 10, 25)
#        sheet.set_column(0, 11, 25)
#        sheet.set_column(0, 12, 25)
        """sheet.set_column(0, 13, 25)
        sheet.set_column(0, 12, 25)
        sheet.set_column(0, 13, 25)
        sheet.set_column(0, 14, 25)
        sheet.set_column(0, 15, 25)"""


        sheet.write(0, 0, 'S/N', bold)
        sheet.write(0, 1, 'Date', bold)
        sheet.write(0, 2, 'Quote No', bold)
        sheet.write(0, 3, 'Customer', bold)
        sheet.write(0, 4, 'Account Manager', bold)
        sheet.write(0, 5, 'Total Cost', bold)
        sheet.write(0, 6, 'Selling Price', bold)
        sheet.write(0, 7, 'Margin', bold)
        """sheet.write(0, 8, 'CP', bold)
        sheet.write(0, 9, 'TCP', bold)
        sheet.write(0, 10, 'SP', bold)
        sheet.write(0, 11, 'TSP', bold)
        sheet.write(0, 12, 'VAT', bold)
        sheet.write(0, 13, 'TP', bold)
        sheet.write(0, 14, 'Margin', bold)
        sheet.write(0, 15, 'Status', bold)"""

        r = 1
        for obj in lines:
            for ord in obj.order_line:
                c = 1
                sheet.write(r, 0, r)
                unix_ts = obj.date_order
                strn = unix_ts.strftime('%m/%d/%Y')
               # dt = (datetime.fromtimestamp(t) - timedelta(hours=2)).strftime('%Y-%m-%d')
                sheet.write(r, c, strn)
                c+=1
                sheet.write(r, c, obj.quote_name)
                c+=1
                if obj.partner_id:
                    sheet.write(r, c, obj.partner_id.name)
                c += 1
                if obj.user_id:
                    sheet.write(r, c, obj.user_id.name)
                c += 1
                if ord.total_purchase_price:
                    sheet.write(r, c, ord.total_purchase_price)
                c += 1
                if ord.price_subtotal:
                    sheet.write(r, c, ord.price_subtotal)
                c += 1
                if ord.profit:
                    sheet.write(r, c, ord.profit)

                """if ord.purchase_price:
                    sheet.write(r, c, ord.purchase_price)
                c += 1
                if ord.total_purchase_price:
                    sheet.write(r, c, ord.total_purchase_price)
                c += 1
                if ord.price_unit:
                    sheet.write(r, c, ord.price_unit)
                c += 1
                if ord.price_subtotal:
                    sheet.write(r, c, ord.price_subtotal)
                c += 1
                #print(ord.tax_id.amount)
                if ord.tax_id:
                    tax_amount = ord.price_subtotal * (ord.tax_id.amount)/100
                    sheet.write(r, c, tax_amount)
                c += 1

                if ord.profit:
                    sheet.write(r, c, ord.profit)
                c += 1
                if ord.margin:
                    sheet.write(r, c, ord.margin)"""


                c += 1
                r += 1

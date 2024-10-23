# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

PAY_LINES_PER_PAGE = 20


class PrintBatchDeposit(models.AbstractModel):
    _name = 'report.account_batch_deposit.print_batch_deposit'
    _template = 'account_batch_deposit.print_batch_deposit'

    def get_pages(self, deposit):
        """ Returns the data structure used by the template
        """
        i = 0
        payment_slices = []
        while i < len(deposit.payment_ids):
            payment_slices.append(deposit.payment_ids[i:i+PAY_LINES_PER_PAGE])
            i += PAY_LINES_PER_PAGE

        return [{
            'date': deposit.date,
            'deposit_name': deposit.name,
            'journal_name': deposit.journal_id.name,
            'payments': payments,
            'currency': deposit.currency_id,
            'total_amount': deposit.amount,
            'footer': deposit.journal_id.company_id.rml_footer,
        } for payments in payment_slices]

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report_name = 'account_batch_deposit.print_batch_deposit'
        report = report_obj._get_report_from_name(report_name)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'pages': self.get_pages,
        }
        return report_obj.render(report_name, docargs)

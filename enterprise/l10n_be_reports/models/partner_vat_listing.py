# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.tools.misc import formatLang


class ReportL10nBePartnerVatListing(models.AbstractModel):
    _name = "l10n.be.report.partner.vat.listing"
    _description = "Partner VAT Listing"

    @api.model
    def get_lines(self, context_id, line_id=None):
        lines = []

        partner_ids = self.env['res.partner'].search([('vat', 'ilike', 'BE%')]).ids
        if not partner_ids:
            return lines

        tag_ids = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in
                   ['l10n_be.tax_tag_00', 'l10n_be.tax_tag_01', 'l10n_be.tax_tag_02', 'l10n_be.tax_tag_03',
                    'l10n_be.tax_tag_45', 'l10n_be.tax_tag_49']]
        tag_ids_2 = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in ['l10n_be.tax_tag_54', 'l10n_be.tax_tag_64']]
        query = """
                    SELECT turnover_sub.partner_id, turnover_sub.name, turnover_sub.vat, turnover_sub.turnover, refund_vat_sub.refund_base, refund_base_sub.vat_amount, refund_base_sub.refund_vat_amount
                    FROM (SELECT l.partner_id, p.name, p.vat, SUM(l.credit - l.debit) as turnover
                          FROM account_move_line l
                          LEFT JOIN res_partner p ON l.partner_id = p.id AND p.customer = true
                          RIGHT JOIN (
                              SELECT DISTINCT amlt.account_move_line_id
                              FROM account_move_line_account_tax_rel amlt
                              LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                              WHERE tt.account_account_tag_id IN %(tags)s
                          ) AS x ON x.account_move_line_id = l.id
                          LEFT JOIN account_invoice inv ON l.invoice_id = inv.id
                          WHERE p.vat IS NOT NULL
                          AND l.partner_id IN %(partner_ids)s
                          AND l.date >= %(date_from)s
                          AND l.date <= %(date_to)s
                          AND l.company_id IN %(company_ids)s
                          AND ((l.invoice_id IS NULL AND l.credit > 0)
                            OR (inv.type IN ('out_refund', 'out_invoice') AND inv.state IN ('open', 'paid')))
                          GROUP BY l.partner_id, p.name, p.vat) AS turnover_sub
                    FULL JOIN (SELECT l.partner_id, SUM(l.debit-l.credit) AS refund_base
                        FROM account_move_line l
                        LEFT JOIN res_partner p ON l.partner_id = p.id AND p.customer = true
                         RIGHT JOIN (
                              SELECT DISTINCT amlt.account_move_line_id
                              FROM account_move_line_account_tax_rel amlt
                              LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                              WHERE tt.account_account_tag_id IN %(tags)s
                          ) AS x ON x.account_move_line_id = l.id
                          LEFT JOIN account_invoice inv ON l.invoice_id = inv.id
                          WHERE p.vat IS NOT NULL
                          AND l.partner_id IN %(partner_ids)s
                          AND l.date >= %(date_from)s
                          AND l.date <= %(date_to)s
                          AND l.company_id IN %(company_ids)s
                          AND ((l.invoice_id IS NULL AND l.credit > 0)
                            OR (inv.type = 'out_refund' AND inv.state IN ('open', 'paid')))
                          GROUP BY l.partner_id, p.name, p.vat) AS refund_vat_sub
                    ON turnover_sub.partner_id = refund_vat_sub.partner_id
                    LEFT JOIN (SELECT l2.partner_id, SUM(l2.credit - l2.debit) as vat_amount, SUM(l2.debit) AS refund_vat_amount
                          FROM account_move_line l2
                          LEFT JOIN account_tax tax2 on l2.tax_line_id = tax2.id
                          LEFT JOIN account_invoice inv ON l2.invoice_id = inv.id
                          WHERE tax2.id IN (SELECT DISTINCT(account_tax_id) from account_tax_account_tag WHERE account_account_tag_id IN %(tags2)s)
                          AND l2.partner_id IN %(partner_ids)s
                          AND l2.date >= %(date_from)s
                          AND l2.date <= %(date_to)s
                          AND l2.company_id IN %(company_ids)s
                          AND ((l2.invoice_id IS NULL AND l2.credit > 0)
                            OR (inv.type IN ('out_refund', 'out_invoice') AND inv.state IN ('open', 'paid')))
                          GROUP BY l2.partner_id) AS refund_base_sub
                    ON turnover_sub.partner_id = refund_base_sub.partner_id
                   WHERE turnover > 250 OR refund_base > 0 OR refund_vat_amount > 0
                """
        params = {
            'tags': tuple(tag_ids),
            'tags2': tuple(tag_ids_2),
            'partner_ids': tuple(partner_ids),
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'company_ids': tuple(context_id.company_ids.ids),
        }
        self.env.cr.execute(query, params)

        for record in self.env.cr.dictfetchall():
            currency_id = self.env.user.company_id.currency_id
            columns = [record['vat'].replace(' ', '').upper(), record['turnover'], record['vat_amount']]
            if not self.env.context.get('no_format', False):
                columns[1] = formatLang(self.env, columns[1] or 0.0, currency_obj=currency_id)
                columns[2] = formatLang(self.env, columns[2] or 0.0, currency_obj=currency_id)
            lines.append({
                'id': record['partner_id'],
                'type': 'partner_id',
                'name': record['name'],
                'footnotes': context_id._get_footnotes('partner_id', record['partner_id']),
                'columns': columns,
                'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
        return lines

    @api.model
    def get_title(self):
        return _('Partner VAT Listing')

    @api.model
    def get_name(self):
        return 'l10n_be_partner_vat_listing'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_date_range_no_comparison')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


class ReportL10nBePartnerVatListingContext(models.TransientModel):
    _name = "l10n.be.partner.vat.listing.context"
    _description = "A particular context for the Partner VAT Listing report"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.env['l10n.be.report.partner.vat.listing']

    def get_columns_names(self):
        return [_('VAT Number'), _('Turnover'), _('VAT Amount')]

    @api.multi
    def get_columns_types(self):
        return ['text', 'number', 'number']

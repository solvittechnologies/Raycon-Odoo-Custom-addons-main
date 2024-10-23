# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.tools.misc import formatLang


class ReportL10nBePartnerVatIntra(models.AbstractModel):
    _name = "l10n.be.report.partner.vat.intra"
    _description = "Partner VAT Intra"

    @api.model
    def get_lines(self, context_id, line_id=None, get_xml_data=False):
        lines = []
        seq = amount_sum = 0
        company_clause = 'AND FALSE'
        if context_id.company_ids.ids:
            company_ids = '(' + ','.join(map(str, context_id.company_ids.ids)) + ')'
            company_clause = 'AND l.company_id IN ' + company_ids
        tag_ids = [self.env['ir.model.data'].xmlid_to_res_id(k) for k in ['l10n_be.tax_tag_44', 'l10n_be.tax_tag_46L', 'l10n_be.tax_tag_46T']]
        if get_xml_data:
            group_by = 'p.vat, intra_code'
            select = ''
        else:
            group_by = 'p.name, l.partner_id, p.vat, intra_code'
            select = 'p.name As partner_name, l.partner_id AS partner_id,'
        query = """
        SELECT {select} p.vat AS vat,
                      tt.account_account_tag_id AS intra_code, SUM(-l.balance) AS amount
                      FROM account_move_line l
                      LEFT JOIN res_partner p ON l.partner_id = p.id
                      LEFT JOIN account_move_line_account_tax_rel amlt ON l.id = amlt.account_move_line_id
                      LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
                      WHERE tt.account_account_tag_id IN %s
                       AND l.date >= '%s'
                       AND l.date <= '%s'
                       %s
                      GROUP BY {group_by}
        """ % (tuple(tag_ids), context_id.date_from, context_id.date_to, company_clause)
        self.env.cr.execute(query.format(select=select, group_by=group_by))
        p_count = 0

        for row in self.env.cr.dictfetchall():
            if not row['vat']:
                row['vat'] = ''
                p_count += 1

            amt = row['amount'] or 0.0
            if amt:
                seq += 1
                amount_sum += amt

                [intra_code, code] = row['intra_code'] == tag_ids[0] and ['44', 'S'] or (row['intra_code'] == tag_ids[1] and ['46L', 'L'] or (row['intra_code'] == tag_ids[2] and ['46T', 'T'] or ['', '']))

                columns = [row['vat'].replace(' ', '').upper(), code, intra_code, amt]
                if not self.env.context.get('no_format', False):
                    currency_id = self.env.user.company_id.currency_id
                    columns[3] = formatLang(self.env, columns[3], currency_obj=currency_id)

                lines.append({
                    'id': row['partner_id'] if not get_xml_data else False,
                    'type': 'partner_id',
                    'name': row['partner_name'] if not get_xml_data else False,
                    'footnotes': context_id._get_footnotes('partner_id', row['partner_id']) if not get_xml_data else False,
                    'columns': columns,
                    'level': 2,
                    'unfoldable': False,
                    'unfolded': False,
                })

        if get_xml_data:
            return {'lines': lines, 'clientnbr': str(seq), 'amountsum': round(amount_sum, 2), 'partner_wo_vat': p_count}
        return lines

    @api.model
    def get_title(self):
        return _('Partner VAT Intra')

    @api.model
    def get_name(self):
        return 'l10n_be_partner_vat_intra'

    @api.model
    def get_report_type(self):
        return self.env.ref('account_reports.account_report_type_date_range_no_comparison')

    @api.model
    def get_template(self):
        return 'account_reports.report_financial'


class ReportL10nBePartnerVatIntraContext(models.TransientModel):
    _name = "l10n.be.partner.vat.intra.context"
    _description = "A particular context for the partner VAT Intra report"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.env['l10n.be.report.partner.vat.intra']

    def get_columns_names(self):
        return [_('VAT Number'), _('Code'), _('Intra Code'), _('Amount')]

    @api.multi
    def get_columns_types(self):
        return ['text', 'text', 'text', 'number']

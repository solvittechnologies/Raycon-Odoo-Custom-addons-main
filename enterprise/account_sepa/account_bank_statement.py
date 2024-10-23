# -*- coding: utf-8 -*-

from odoo import models
from sepa_credit_transfer import prepare_SEPA_string


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def _get_communication(self, payment_method_id):
        if payment_method_id and payment_method_id == self.env.ref('account_sepa.account_payment_method_sepa_ct'):
            return prepare_SEPA_string(self.name or '')[:140]
        return super(AccountBankStatementLine, self)._get_communication(payment_method_id)

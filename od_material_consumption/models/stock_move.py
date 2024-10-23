from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    # def _account_entry_move(self, qty, description, svl_id, cost):
    def _account_entry_move(self):
        """ Accounting Valuation Entries """
        if not self.inventory_id.is_material_consumption:
            return super(StockMove, self)._account_entry_move()

        res = super(StockMove, self)._account_entry_move()
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = self.mapped('move_line_ids.location_id.company_id') if self._is_out() else False
        company_to = self.mapped('move_line_ids.location_dest_id.company_id') if self._is_in() else False

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
                if location_from and location_from.usage == 'customer':  # goods returned from customer
                    self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation,
                                                                                             journal_id)
                    # self.with_context(force_company=company_to.id)._create_account_move_line(expense_account, stock_input,
                    #                                                                          journal_id)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src, journal_id)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if self._is_dropshipped():
                self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest, journal_id)
            elif self._is_dropshipped_returned():
                self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_dest, acc_src, journal_id)

        if self.company_id.anglo_saxon_accounting:
            # eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            allowed_invoice_types = self._is_in() and ('in_invoice', 'out_refund') or ('in_refund', 'out_invoice')
            self._get_related_invoices().filtered(
                lambda x: x.type in allowed_invoice_types)._anglo_saxon_reconcile_valuation(product=self.product_id)
            return res
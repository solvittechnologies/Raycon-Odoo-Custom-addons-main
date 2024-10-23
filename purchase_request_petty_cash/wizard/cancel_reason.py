from odoo import models, fields, api

class PurchaseRequestPettyCashCancel(models.TransientModel):
    _name = 'purchase.request.petty.cash.cancel'

    reason = fields.Text(
        string='Reason',
        required=True)

    @api.multi
    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        pr_pc_ids = self._context.get('active_ids')
        if pr_pc_ids is None:
            return act_close
        assert len(pr_pc_ids) == 1, "Only 1 Petty Cash expected"
        pr_pc_id = self.env['kay.petty.cash'].browse(pr_pc_ids)
        pr_pc_id.cancel_reason = self.reason
        pr_pc_id.button_rejected()
        return act_close

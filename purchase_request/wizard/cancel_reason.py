from odoo import models, fields, api

class PurchaseRequestCancel(models.TransientModel):

    """ Ask a reason for the Purchase Request cancellation."""
    _name = 'purchase.request.cancel'
    _description = __doc__

    reason = fields.Text(
        string='Reason',
        required=True)

    @api.multi
    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        pr_ids = self._context.get('active_ids')
        if pr_ids is None:
            return act_close
        assert len(pr_ids) == 1, "Only 1 Purchase Request expected"
        pr_id = self.env['purchase.request'].browse(pr_ids)
        pr_id.cancel_reason = self.reason
        pr_id.button_rejected()
        return act_close

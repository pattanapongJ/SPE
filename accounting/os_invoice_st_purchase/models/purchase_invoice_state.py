from odoo import fields, models, api, _


class PurchaseInherit(models.Model):
    _inherit = 'purchase.order'

    payment_state = fields.Selection(
        selection=[
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        string="Payment Status",
        compute='_compute_payment_state', store=True, readonly=True,
        copy=False,
        tracking=True,
    )

    @api.depends('invoice_ids.payment_state')
    def _compute_payment_state(self):
        for rec in self:
            payment_states = [x.payment_state for x in rec.invoice_ids]
            if not len(payment_states) == 0:
                if len(payment_states) == 1:
                    rec.payment_state = payment_states[0]
                else:
                    if all(element == payment_states[0] for element in
                           payment_states):
                        rec.payment_state = payment_states[0]
                    elif 'partial' in payment_states:
                        rec.payment_state = 'partial'
                    else:
                        rec.payment_state = 'in_payment'
            else:
                rec.payment_state = False

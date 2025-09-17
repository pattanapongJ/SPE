from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    "out_invoice": "customer",
    "in_invoice": "supplier",
}

BILL_TYPE = ["out_invoice", "in_invoice", "out_refund", "in_refund"]


class AccountBilling(models.Model):
    _name = "account.group.billing"
    _description = "Account Group Billing"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"

    name = fields.Char(
        readonly=True,
        copy=False,
        help="Number of account.group.billing",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        help="Partner Information",
        tracking=True,
    )
    date = fields.Date(
        string="Billing Date",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.context_today,
        help="Effective date for accounting entries",
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
        help="Leave this field empty if this route is shared \
            between all companies",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("cancel", "Cancelled"), ("billed", "Billed")],
        string="Status",
        readonly=True,
        default="draft",
        help="""
            * The 'Draft' status is used when a user create a new billing\n
            * The 'Billed' status is used when user confirmed billing,
                billing number is generated\n
            * The 'Cancelled' status is used when user billing is cancelled
        """,
    )
    narration = fields.Text(
        string="Notes",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Notes",
    )
    billing_line_ids = fields.One2many(
        comodel_name="account.group.billing.line",
        inverse_name="billing_id",
        string="Bill Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    invoice_related_count = fields.Integer(
        string="# of Invoices",
        compute="_compute_invoice_related_count",
        help="Count invoice in billing",
    )
    branch = fields.Many2one('res.branch', string='Branch', check_company=True)
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.billing_line_ids = False

    def _compute_invoice_related_count(self):
        self.invoice_related_count = len(self.billing_line_ids)

    def name_get(self):
        result = [(billing.id, (billing.name or "Draft")) for billing in self]
        return result

    def validate_billing(self):
        for rec in self:
            seq_code = "account.group.billing"
            rec.name = (
                self.env["ir.sequence"]
                .with_context(ir_sequence_date=fields.Date.today())
                .next_by_code(seq_code)
            )
            rec.write({"state": "billed"})
            rec.message_post(body=_("Billing is billed."))
        return True

    def action_cancel_draft(self):
        for rec in self:
            rec.write({"state": "draft"})
            rec.message_post(body=_("Billing is reset to draft"))
        return True

    def action_cancel(self):
        for rec in self:
            invoice_paid = rec.billing_line_ids.mapped("invoice_id").filtered(
                lambda l: l.payment_state == "paid"
            )
            if invoice_paid:
                raise ValidationError(_("Invoice paid already."))
            rec.write({"state": "cancel"})
            self.message_post(body=_("Billing %s is cancelled") % rec.name)
        return True

    def invoice_relate_billing_tree_view(self):
        return {
            "name": _("Group Biling"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "views": [
                (self.env.ref("account.view_move_tree").id, "tree"),
                (self.env.ref("account.view_move_form").id, "form"),
            ],
            "type": "ir.actions.act_window",
            "domain": [
                ("id", "in", [rec.invoice_id.id for rec in self.billing_line_ids])
            ],
            "context": {"create": False},
        }
        
    def get_domain(self):
        selected_invoice_ids = self.billing_line_ids.mapped('invoice_id.id')

        if self.billing_line_ids.invoice_id:
            selected_invoice_ids += self.billing_line_ids.invoice_id.ids 
        domain = [
            # ('partner_id', '=', self.partner_id.id),
            ('payment_state', '!=', 'paid'),
            ('state', '=', 'posted'),
            ('move_type', 'in', BILL_TYPE),
            ('id', 'not in', selected_invoice_ids)
        ]
        
        return domain


class AccountBillingLine(models.Model):
    _name = "account.group.billing.line"
    _description = "Billing Line"

    billing_id = fields.Many2one(comodel_name="account.group.billing")
    invoice_id = fields.Many2one(comodel_name="account.move")
    name = fields.Char(related="invoice_id.name")
    invoice_date = fields.Date(related="invoice_id.invoice_date")
    threshold_date = fields.Date(related="invoice_id.invoice_date_due")
    origin = fields.Char(related="invoice_id.invoice_origin")
    total = fields.Float()
    state = fields.Selection(related="invoice_id.state")
    payment_state = fields.Selection(related="invoice_id.payment_state")

    @api.onchange('invoice_id')
    def _get_invoice_domain(self): 
        domain = []
        active_bill_id = self.billing_id._origin.id or self.billing_id.id
        if not active_bill_id:
            domain = self.billing_id.get_domain()
        else:
            # current active bill
            active_bill = self.billing_id

            partner_id = active_bill.partner_id.id
            
            selected_invoice_ids = active_bill.billing_line_ids.mapped('invoice_id.id')

            if self.invoice_id:
                selected_invoice_ids += self.invoice_id.ids
            
            domain = [
                # ('partner_id', '=', partner_id),
                ('payment_state', '!=', 'paid'),
                ('state', '=', 'posted'),
                ('move_type', '=', BILL_TYPE),
                ('id', 'not in', selected_invoice_ids)
            ]
            
        amount = self.invoice_id.amount_residual
        if self.invoice_id.move_type in ["out_refund", "in_refund"]:
            amount *= (-1)
        self.total = amount
            
        return {'domain': {'invoice_id': domain}}
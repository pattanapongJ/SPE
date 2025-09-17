# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import qrcode
import base64
from io import StringIO, BytesIO, TextIOWrapper
from werkzeug.urls import url_encode
import uuid

class HrExpense(models.Model):
    _inherit = "hr.expense"

    sheet_id_state = fields.Selection(related="sheet_id.state", string="Sheet state")
    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Vendor Bill",
        domain=[
            ("move_type", "=", "in_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "=", "not_paid"),
            ("expense_ids", "=", False),
        ],
        copy=False,
    )
    contact_person = fields.Many2one(
        'res.partner', string='Contact Person', readonly=False)

    def action_expense_create_invoice(self):
        invoice_lines = [
            (
                0,
                0,
                {
                    "product_id": self.product_id.id,
                    "name": self.name,
                    "price_unit": self.unit_amount,
                    "quantity": self.quantity,
                    "account_id": self.account_id.id,
                    "analytic_account_id": self.analytic_account_id.id,
                    "tax_ids": [(6, 0, self.tax_ids.ids)],
                },
            )
        ]
        invoice = self.env["account.move"].create(
            [
                {
                    "ref": self.reference,
                    "move_type": "in_invoice",
                    "invoice_date": self.date,
                    "invoice_line_ids": invoice_lines,
                }
            ]
        )
        self.write(
            {
                "invoice_id": invoice.id,
                "quantity": 1,
                "tax_ids": False,
                "unit_amount": invoice.amount_total,
            }
        )
        return True

    @api.constrains("invoice_id")
    def _check_invoice_id(self):
        for expense in self:  # Only non binding expense
            if (
                not expense.sheet_id
                and expense.invoice_id
                and expense.invoice_id.state != "posted"
            ):
                raise UserError(_("Vendor bill state must be Posted"))

    def _get_account_move_line_values(self):
        """It overrides the journal item values to match the invoice payable one."""
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense_id, move_lines in move_line_values_by_expense.items():
            expense = self.browse(expense_id)
            if not expense.invoice_id:
                continue
            for move_line in move_lines:
                if move_line["debit"]:
                    move_line[
                        "partner_id"
                    ] = expense.invoice_id.partner_id.commercial_partner_id.id
                    move_line["account_id"] = expense.invoice_id.line_ids.filtered(
                        lambda l: l.account_internal_type == "payable"
                    ).account_id.id
        return move_line_values_by_expense

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        """Get expense amount from invoice amount. Otherwise it will do a
        mismatch when trying to post the account move. We do that ensuring we
        have the same total amount with quantity 1 and without taxes.
        """
        if self.invoice_id:
            self.quantity = 1
            self.tax_ids = [(5,)]
            # Assign this amount after removing taxes for avoiding to raise
            # the constraint _check_expense_ids
            self.unit_amount = self.invoice_id.amount_total
    
    def action_print_expense(self):
        return self.env.ref('hr_expense_invoice.expense_report').report_action(self)

    def generate_qr_code(self, invoice):
        # Create the QR code image
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,
                           border=4,)
        qr.add_data(invoice)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Encode the image as a base64 string
        with BytesIO() as buffer:
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
    
    access_url = fields.Char(
        'Portal Access URL', compute='_compute_access_url',
        help='Customer Portal URL')
    access_token = fields.Char('Security Token', copy=False)

    # to display the warning from specific model
    access_warning = fields.Text("Access warning", compute="_compute_access_warning")

    def _compute_access_warning(self):
        for mixin in self:
            mixin.access_warning = ''

    def _compute_access_url(self):
        for record in self:
            record.access_url = '#'

    def _portal_ensure_token(self):
        """ Get the current record access token """
        if not self.access_token:
            # we use a `write` to force the cache clearing otherwise `return self.access_token` will return False
            self.sudo().write({'access_token': str(uuid.uuid4())})
        return self.access_token

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None, share_token=True):
        """
        Build the url of the record  that will be sent by mail and adds additional parameters such as
        access_token to bypass the recipient's rights,
        signup_partner to allows the user to create easily an account,
        hash token to allow the user to be authenticated in the chatter of the record portal view, if applicable
        :param redirect : Send the redirect url instead of the direct portal share url
        :param signup_partner: allows the user to create an account with pre-filled fields.
        :param pid: = partner_id - when given, a hash is generated to allow the user to be authenticated
            in the portal chatter, if any in the target page,
            if the user is redirected to the portal instead of the backend.
        :return: the url of the record with access parameters, if any.
        """
        self.ensure_one()
        params = {
            'model': self._name,
            'res_id': self.id,
        }
        if share_token and hasattr(self, 'access_token'):
            params['access_token'] = self._portal_ensure_token()
        if pid:
            params['pid'] = pid
            params['hash'] = self._sign_token(pid)
        if signup_partner and hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])

        return '%s?%s' % ('/mail/view' if redirect else self.access_url, url_encode(params))
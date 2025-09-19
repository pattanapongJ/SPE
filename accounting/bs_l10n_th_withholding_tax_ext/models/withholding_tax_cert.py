# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


INCOME_TAX_FORM = [
    ("pnd1", "PND1"),
    ("pnd1a", "PND1A"),
    ("pnd2", "PND2"),
    ("pnd2a", "PND2A"),
    ("pnd3", "PND3"),
    ("pnd3a", "PND3a"),
    ("pnd53", "PND53"),
]

class WithholdingTaxCert(models.Model):

    _inherit = 'withholding.tax.cert'
    _description = "Withholding Tax Certificate"

    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        string="Income Tax Form",
        required=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    tax_payer = fields.Selection(
        selection_add=[
            ("paid_all_time", "Paid All Time")
        ],
        ondelete={'paid_all_time': 'set default'}
    )
    
    
    @api.depends("payment_id", "move_id")
    def _compute_wt_cert_data(self):
        wt_account_ids = self._context.get("wt_account_ids", [])
        wt_ref_id = self._context.get("wt_ref_id", False)
        income_tax_form = self._context.get("income_tax_form", False)
        CertLine = self.env["withholding.tax.cert.line"]
        Cert = self.env["withholding.tax.cert"]
        certlines = self.env["withholding.tax.cert.line"]
        if wt_account_ids:
            wt_reference = Cert.browse(wt_ref_id)
            for record in self:
                # Hook to find wt move lines
                wt_move_lines = record._get_wt_move_line(
                    record.payment_id, record.move_id, wt_account_ids
                )
                partner_id = record.payment_id.partner_id or record.move_id.partner_id
                # WHT from journal entry, use partner from line.
                if record.move_id and record.move_id.move_type == "entry":
                    partner = wt_move_lines.mapped("partner_id")
                    if len(partner) == 1:
                        partner_id = wt_move_lines[0].partner_id

                record.update(
                    {
                        "name": record.payment_id.name or record.move_id.name,
                        "date": record.payment_id.date or record.move_id.date,
                        "ref_wt_cert_id": wt_reference or False,
                        "supplier_partner_id": partner_id,
                        "income_tax_form": income_tax_form,
                    }
                )
                for line in wt_move_lines:
                    certlines += CertLine.new(record._prepare_wt_line(line))
                ##Group By WH TAX
                # wt_tax_ids = wt_move_lines.mapped("wt_tax_id")
                # for wt_tax in wt_tax_ids:
                #     gp_wt_move_lines = wt_move_lines.filtered(lambda x:x.wt_tax_id == wt_tax)
                #     if gp_wt_move_lines:
                #         total_balance = sum(gp_wt_move_lines.mapped("balance"))
                #         cert_line_val = record._prepare_wt_line(gp_wt_move_lines[0])
                #         cert_line_val.update({
                #             "amount": abs(total_balance),
                #             "base": (abs(total_balance) / wt_tax.amount * 100) if wt_tax.amount else False,
                #         })
                #         certlines += CertLine.new(cert_line_val)
                record.wt_line = certlines
                
    


class WithholdingTaxCertLine(models.Model):
    _inherit = 'withholding.tax.cert.line'
    
    
    is_manual_base_amount = fields.Boolean('Manual Base Amount', default=False)
    
    @api.constrains("base", "wt_percent", "amount")
    def _check_wt_line(self):
        filtered_lines = self.filtered(lambda x:not x.is_manual_base_amount)
        return super(WithholdingTaxCertLine,filtered_lines)._check_wt_line()

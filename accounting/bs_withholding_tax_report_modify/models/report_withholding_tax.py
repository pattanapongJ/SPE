from odoo import api, fields, models

class WithHoldingTaxReport(models.TransientModel):
    _inherit =  "withholding.tax.report"

    def _create_text_modify(self, docs):
       self.ensure_one()
       for obj in docs:
            text = ""
            for idx, line in enumerate(obj.results):
                cancel = line.cert_id.state == "cancel"
                text +="{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                    idx + 1,
                    not cancel and line.cert_id.supplier_partner_id.vat or '',
                    not cancel and line.cert_id.supplier_partner_id.name or '',
                    not cancel and line.cert_id.supplier_partner_id.street or '',
                    not cancel and line.cert_id.supplier_partner_id.street2 or '',
                    not cancel and line.cert_id.supplier_partner_id.city or '',
                    not cancel and line.cert_id.supplier_partner_id.state_id.name or '',
                    not cancel and line.cert_id.supplier_partner_id.zip or '',
                    not cancel and line.cert_id.supplier_partner_id.branch or '',
                    not cancel and self.format_date_dmy(line.cert_id.date) or '',
                    not cancel and line.wt_cert_income_desc or '',
                    not cancel and "{:,.2f}".format(line.wt_percent) or 0.00,
                    not cancel and "{:,.2f}".format(line.base) or 0.00,
                    not cancel and "{:,.2f}".format(line.amount) or 0.00,
                    not cancel and self._convert_tax_payer(line.cert_id.tax_payer) or '',
                    not cancel and line.cert_id.payment_id or '',
                )
            return text
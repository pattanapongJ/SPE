# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class WithholdingTaxReportXslx(models.AbstractModel):
    _name = "report.withholding.tax.report.xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Withholding Tax xlsx"

    def _define_formats(self, workbook):
        super()._define_formats(workbook)
        date_format = "DD/MM/YYYY"
        FORMATS["format_date_dmy_right"] = workbook.add_format(
            {"align": "right", "num_format": date_format}
        )

    def _get_ws_params(self, wb, data, obj):
        withholding_tax_template = {
            "01_sequence": {
                "header": {"value": "No."},
                "data": {
                    "value": self._render("sequence"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 3,
            },
            "02_vat": {
                "header": {"value": "Tax ID"},
                "data": {
                    "value": self._render("vat"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 16,
            },
            "03_a_title": {
                "header": {"value": "Title"},
                "data": "",
                "width": 10,
            },
            "03_display_name": {
                "header": {"value": "Name"},
                "data": {"value": self._render("display_name")},
                "width": 18,
            },
            "04_street": {
                "header": {"value": "Street"},
                "data": {"value": self._render("street")},
                "width": 20,
            },
            "05_street2": {
                "header": {"value": "Street2"},
                "data": {"value": self._render("street2")},
                "width": 20,
            },
            "06_city": {
                "header": {"value": "City"},
                "data": {"value": self._render("city")},
                "width": 20,
            },
            "07_state": {
                "header": {"value": "State"},
                "data": {"value": self._render("state")},
                "width": 20,
            },            
            "08_zip": {
                "header": {"value": "Zip"},
                "data": {"value": self._render("zip")},
                "width": 20,
            },   
            "09_branch": {
                "header": {"value": "Branch"},
                "data": {"value": self._render("branch")},
                "width": 20,
            },                               
            "10_date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("date"),
                    "type": "datetime",
                    "format": FORMATS["format_date_dmy_right"],
                },
                "width": 10,
            },
            "11_income_desc": {
                "header": {"value": "Income Description"},
                "data": {"value": self._render("income_desc")},
                "width": 18,
            },
            "12_tax": {
                "header": {"value": "Tax"},
                "data": {
                    "value": self._render("tax*100"),
                    "type": "number",
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 8,
            },
            "13_base_amount": {
                "header": {"value": "Base Amount"},
                "data": {
                    "value": self._render("base_amount"),
                    "type": "number",
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 13,
            },
            "14_tax_amount": {
                "header": {"value": "Tax Amount"},
                "data": {
                    "value": self._render("tax_amount"),
                    "type": "number",
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 13,
            },
            "15_WHT Condition": {
                "header": {"value": "WHT Condition"},
                "data": {"value": 1},
                "width": 19,
            },
            "16_payment_id": {
                "header": {"value": "Doc Ref."},
                "data": {"value": self._render("payment_id")},
                "width": 19,
            },
        }

        ws_params = {
            "ws_name": "Withholding Tax Report",
            "generate_ws_method": "_withholding_tax_report",
            "title": "Withholding Tax Report - %s" % (obj.company_id.name),
            "wanted_list": [x for x in sorted(withholding_tax_template.keys())],
            "col_specs": withholding_tax_template,
        }

        return [ws_params]

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 1, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_center"])
            ws.merge_range(row_pos, 2, row_pos, 3, "")
            ws.write_row(row_pos, 2, [data[1]], FORMATS["format_center"])
            row_pos += 1
        return row_pos + 1

    def _write_ws_lines(self, row_pos, ws, ws_params, obj):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)
        index = 1
        for line in obj.results:
            cancel = line.cert_id.state == "cancel"
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "sequence": index,
                    "vat": not cancel and line.cert_id.supplier_partner_id.vat or "",
                    "display_name": not cancel and line.cert_id.supplier_partner_id.name or "Cancelled",
                    "street": not cancel and line.cert_id.supplier_partner_id.street or "",
                    "street2": not cancel and line.cert_id.supplier_partner_id.street2 or "",
                    "city": not cancel and line.cert_id.supplier_partner_id.city or "",
                    "state": not cancel and line.cert_id.supplier_partner_id.state_id.name or "",
                    "zip": not cancel and line.cert_id.supplier_partner_id.zip or "",
                    "branch": not cancel and line.cert_id.supplier_partner_id.branch or "",
                    "date": not cancel and line.cert_id.date,
                    "income_desc": not cancel and line.wt_cert_income_desc or "",
                    "tax": not cancel and line.wt_percent / 100 or 0.00,
                    "base_amount": not cancel and line.base or 0.00,
                    "tax_amount": not cancel and line.amount or 0.00,
                    "tax_payer": not cancel and line.cert_id.tax_payer,
                    "payment_id": not cancel and line.cert_id.name,
                },
                default_format=FORMATS["format_tcell_left"],
            )
            index += 1
        return row_pos

    def _write_ws_footer(self, row_pos, ws, obj):
        results = obj.results.filtered(lambda l: l.cert_id.state == "done")
        ws.merge_range(row_pos, 0, row_pos, 6, "")
        ws.merge_range(row_pos, 9, row_pos, 10, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        ws.write_row(
            row_pos,
            7,
            [sum(results.mapped("base")), sum(results.mapped("amount")), ""],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _withholding_tax_report(self, workbook, ws, ws_params, data, obj):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        row_pos = 0
        header_data_list = [
            (
                "Date range filter",
                obj.date_from.strftime("%d/%m/%Y")
                + " - "
                + obj.date_to.strftime("%d/%m/%Y"),
            ),
            ("Income Tax Form", obj.income_tax_form),
            ("Currency", obj.company_id.currency_id.name),
            ("Tax ID", obj.company_id.partner_id.vat or "-"),
            ("Branch ID", obj.company_id.partner_id.branch or "-"),
        ]
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(row_pos, ws, ws_params, obj)
        row_pos = self._write_ws_footer(row_pos, ws, obj)
        return row_pos

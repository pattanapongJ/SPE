import logging

from odoo import models
from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportTaxReportXlsx(models.TransientModel):
    _inherit = "report.l10n_th_tax_report.report_tax_report_xlsx"

    def _get_ws_params(self, wb, data, objects):
        partner_name = "Partner Name"
        if objects.tax_id.type_tax_use == "sale":
            partner_name = "ชื่อผู้ซื้อสินค้า/ผู้รับบริการ"
        elif objects.tax_id.type_tax_use == "purchase":
            partner_name = "ชื่อผู้ขายสินค้า/ผู้ให้บริการ"

        tax_template = {
            "1_index": {
                "header": {"value": "ลำดับที่"},
                "data": {"value": self._render("row_pos")},
                "width": 7,
            },
            "2_tax_date": {
                "header": {"value": "วัน/เดือน/ปี"},
                "data": {"value": self._render("tax_date")},
                "width": 12,
            },
            "3_tax_invoice": {
                "header": {"value": "เล่มที่/เลขที่"},
                "data": {"value": self._render("tax_invoice_number")},
                "width": 18,
            },
            "4_tax_move": {
                "header": {"value": "Voucher"},
                "data": {"value": self._render("voucher_no")},
                "width": 18,
            },
            "5_partner_name": {
                "header": {"value": partner_name},
                "data": {"value": self._render("partner_name")},
                "width": 30,
            },
            "6_partner_vat": {
                "header": {"value": "ผู้เสียภาษีอากร"},
                "data": {"value": self._render("partner_vat")},
                "width": 15,
            },
            "7_partner_branch": {
                "header": {"value": "สถานประกอบการ"},
                "data": {"value": self._render("partner_branch")},
                "width": 15,
            },
            "8_tax_base_amount": {
                "header": {"value": "มูลค่าสินค้า"},
                "data": {
                    "value": self._render("tax_base_amount"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 18,
            },
            "9_tax_amount": {
                "header": {"value": "จำนวนเงิน"},
                "data": {
                    "value": self._render("tax_amount"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 18,
            },
            "9_total_amount": {
                "header": {"value": "จำนวนเงินรวม"},
                "data": {"value": self._render("total"), "format": FORMATS["format_tcell_amount_right"]},
                "width": 18,
            },
        }
        ws_params = {
            "ws_name": "TAX Report",
            "generate_ws_method": "_vat_report",
            "title": "TAX Report",
            "wanted_list": [k for k in sorted(tax_template.keys())],
            "col_specs": tax_template,
        }
        if objects.tax_id.type_tax_use == "sale":
            ws_params["ws_name"] = "รายงานภาษีขาย"
            ws_params["title"] = "รายงานภาษีขาย"
        elif objects.tax_id.type_tax_use == "purchase":
            ws_params["ws_name"] = "รายงานภาษีซื้อ"
            ws_params["title"] = "รายงานภาษีซื้อ"

        return [ws_params]

    def _vat_report(self, wb, ws, ws_params, data, objects):
        for format in wb.formats:
            format.font_name = 'Kanit Light'
            format.text_wrap = True
            format.text_v_align = 2

        # Adjust column widths (example)

        ws.set_portrait()
        ws.fit_to_pages(1, 0)

        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)

        row_pos = 0
        # title
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)

        # company data
        ws.write_column(
            row_pos, 0, ["ชื่อผู้ประกอบการ :", "ชื่อสถานที่ประกอบการ :"], FORMATS["format_left_bold"]
        )
        ws.write_column(
            row_pos,
            1,
            [
                (objects.company_id.display_name) or "",
                (objects.company_id.display_name) or "",
            ],
        )
        ws.write_column(
            row_pos, 8, [
                f"เดือนภาษี {objects.date_range_id._get_month_thai()}",
                "เลขประจำตัวผู้เสียภาษี",

            ],
            FORMATS["format_left_bold"]
        )
        ws.write_column(
            row_pos + 2, 8, [
                "[/]"
            ],
            FORMATS["format_right_bold"]
        )
        branch_info = f"{objects.branch_id.display_name or ''} {objects.branch_id.branch_no or ''}"
        date_range_year = f"ปี {objects.date_range_id.year_th or ''}"
        ws.write_column(
            row_pos,
            9,
            [
                date_range_year,
                (objects.company_id.vat) or "",
                branch_info

            ],
        )
        partner_name = "Partner Name"
        if objects.tax_id.type_tax_use == "sale":
            partner_name = "ชื่อผู้ซื้อสินค้า/ผู้รับบริการ"
        elif objects.tax_id.type_tax_use == "purchase":
            partner_name = "ชื่อผู้ขายสินค้า/ผู้ให้บริการ"

        row_pos += 3
        FORMATS['format_theader_blue_center'].text_v_align = 2
        FORMATS['format_theader_blue_amount_right'].text_v_align = 2
        ws.merge_range(row_pos, 0, row_pos + 1, 0, "ลำดับที่", FORMATS['format_theader_blue_center'])
        ws.merge_range(row_pos, 1, row_pos, 3, "ใบกำกับภาษี", FORMATS['format_theader_blue_center'])
        ws.merge_range(row_pos, 4, row_pos + 1, 4, partner_name,
                       FORMATS['format_theader_blue_center'])
        ws.write_column(
            row_pos,
            5,
            [
                "เลขประจำตัว",
                "ผู้เสียภาษีอากร"
            ],
            FORMATS['format_theader_blue_center']
        )
        ws.merge_range(row_pos, 6, row_pos + 1, 6, "สถานประกอบการ", FORMATS['format_theader_blue_center'])
        ws.write_column(
            row_pos,
            7,
            [
                "มูลค่าสินค้า",
                "หรือบริการ"
            ],
            FORMATS['format_theader_blue_amount_right']
        )
        ws.write_column(
            row_pos,
            8,
            [
                "จำนวนเงิน",
                "ภาษีมูลค่าเพิ่ม"
            ],
            FORMATS['format_theader_blue_amount_right']
        )

        ws.merge_range(row_pos, 9, row_pos + 1, 9, "จำนวนเงินรวม", FORMATS['format_theader_blue_amount_right'])
        row_pos += 1
        ws.write(row_pos, 1, "วัน/เดือน/ปี", FORMATS['format_theader_blue_center'])
        ws.write(row_pos, 2, "เล่มที่/เลขที่", FORMATS['format_theader_blue_center'])
        ws.write(row_pos, 3, "Voucher", FORMATS['format_theader_blue_center'])
        row_pos += 1

        ws.freeze_panes(row_pos, 0)
        for obj in objects:
            total_base = 0.00
            total_tax = 0.00
            for line in obj.get_line_data():
                total_base += line['tax_base_amount']
                total_tax += line['tax_amount']

                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "row_pos": row_pos - 6,
                        "tax_date": line['tax_date'] or "",
                        "tax_invoice_number": line['tax_invoice_number'] or "",
                        "voucher_no": "\n ".join(line['voucher_no']) or "",
                        "partner_name": line['partner'].name or "",
                        "partner_vat": line['partner'].vat or "",
                        "partner_branch": line['partner'].branch or "",
                        "tax_base_amount": line['tax_base_amount'] or 0.00,
                        "tax_amount": line['tax_amount'] or 0.00,
                        "total": (line['tax_amount'] + line['tax_base_amount']),
                    },
                    default_format=FORMATS["format_tcell_left"],
                )

        ws.write_row(
            row_pos,
            6,
            ['ยอดรวมทั้งหมด :', total_base, total_tax, (total_base + total_tax)],
            FORMATS["format_theader_blue_amount_right"],
        )

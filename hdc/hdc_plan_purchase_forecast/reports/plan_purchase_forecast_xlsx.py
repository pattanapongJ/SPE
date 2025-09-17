from odoo import _, models
from datetime import date, datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

class PlanPurchaseForecastXLSX(models.AbstractModel):
    _name = "report.plan_purchase_forecast_xlsx"
    _description = "Plan Purchase Forecast XLSX Report"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, value):

        # months 4 - 10
        month_remain = date.today() + relativedelta(months = 1)
        month_val0 = date.today()
        month_val1 = date.today() - relativedelta(months = 1)
        month_val2 = date.today() - relativedelta(months = 2)
        month_val3 = date.today() - relativedelta(months = 3)
        month_val4 = date.today() - relativedelta(months = 4)
        month_val5 = date.today() - relativedelta(months = 5)
        month_val6 = date.today() - relativedelta(months = 6)
        month_val7 = date.today() - relativedelta(months = 7)
        month_val8 = date.today() - relativedelta(months = 8)
        month_val9 = date.today() - relativedelta(months = 9)
        month_val10 = date.today() - relativedelta(months = 10)
        month_val11 = date.today() - relativedelta(months = 11)
        # format
        top_cell_format = workbook.add_format({"bold": True, "align": "center", "border": True})
        top_cell_format.set_font_size(16)
        top_cell_format.set_align("vcenter")
        head_cell_format = workbook.add_format({"align": "center", "border": True})
        head_cell_format.set_font_size(12)
        head_cell_format.set_align("vcenter")
        data_cell_format = workbook.add_format({"border": True})
        data_cell_format_right = workbook.add_format({"align": "right", "border": True})

        format_footerC_bold2_2_2 = workbook.add_format({"align": "center", "bottom": True, "left": True, "right": True})
        format_footerC_bold2_2_3 = workbook.add_format({"align": "center", "left": True, "right": True})
        format_footerC_bold2_2_3.set_font_size(11)
        format_footerC_bold2_2_3.set_font_size(11)

        # report name
        report_name = "PLAN PURCHASE"
        sheet = workbook.add_worksheet(report_name)
        sheet.set_row(0, 20)
        if value.date_before == "four":
            for rec in range(33):
                sheet.set_column(0, rec, 15)

            sheet.write(0, 0, "Item number", head_cell_format)
            sheet.write(0, 1, "Product name", head_cell_format)
            sheet.write(0, 2, "Inventory unit", head_cell_format)
            sheet.write(0, 3, "Vendor", head_cell_format)
            sheet.write(0, 4, "Origin", head_cell_format)
            sheet.write(0, 5, "To Order", head_cell_format)
            sheet.write(0, 6, "To Stock", head_cell_format)
            sheet.write(0, 7, "Physical packing Qty", head_cell_format)
            sheet.write(0, 8, "Physical packing Unit", head_cell_format)
            sheet.write(0, 9, "สินค้าค้างส่งยกมา", head_cell_format)
            sheet.write(0, 10, "SO %s" %calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 11, "SO %s" %calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 12, "SO %s" %calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 13, "SO %s" %calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 14, "SO Remain", head_cell_format)
            sheet.write(0, 15, "SO SUM", head_cell_format)
            sheet.write(0, 16, "สินค้าค้างรับยกมา", head_cell_format)
            sheet.write(0, 17, "PO %s" %calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 18, "PO %s" %calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 19, "PO %s" %calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 20, "PO %s" %calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 21, "PO Total", head_cell_format)
            sheet.write(0, 22, "QTY.%s" %calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 23, "QTY.%s" %calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 24, "QTY.%s" %calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 25, "QTY.%s" %calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 26, "QTY.SUM", head_cell_format)
            sheet.write(0, 27, "Sale out/M", head_cell_format)
            sheet.write(0, 28, "STOCK", head_cell_format)
            sheet.write(0, 29, "จำนวนเดือนที่ขายได้(S/T)", head_cell_format)
            sheet.write(0, 30, "จำนวนเดือนที่ขายได้(S/T+B/O)", head_cell_format)
            sheet.write(0, 31, "สั่งซื้อใหม่", head_cell_format)
            sheet.write(0, 32, "จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ)", head_cell_format)

            product_id = self.env["product.product"].search([("type", "=", "product")])
            # for test one product
            # product_id = self.env["product.product"].search([("type", "=", "product"),("default_code", "=", "AABFBT42V042I4")])

            # so search --------------------------

            out_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])



            out_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")),
                 ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val0.year, month_val0.month,
                                                                             calendar.monthrange(month_val0.year,
                                                                                                 month_val0.month)[
                                                                                 1]))])
            out_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")),
                 ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val1.year, month_val1.month,
                                                                             calendar.monthrange(month_val1.year,
                                                                                                 month_val1.month)[
                                                                                 1]))])

            out_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")),
                 ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val2.year, month_val2.month,
                                                                             calendar.monthrange(month_val2.year,
                                                                                                 month_val2.month)[
                                                                                 1]))])

            out_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")),
                 ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val3.year, month_val3.month,
                                                                             calendar.monthrange(month_val3.year,
                                                                                                 month_val3.month)[
                                                                                 1]))])

            out_remain_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_remain.year, month_remain.month))])

            # so search state -------------------------- by invoice post
            out_move1_all_not_state = self.env["account.move.line"].search([
                ("parent_state", "=", "posted"),("move_id.move_type", "=", "out_invoice"),
                ("move_id.invoice_date", ">=","%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)),
                ("move_id.invoice_date", "<=","%s-%s-%s 23:59:59"%(month_val0.year, month_val0.month,
                                                                             calendar.monthrange(month_val0.year,
                                                                                                 month_val0.month)[1]))])
            out_move2_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                    ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                month_val1.year, month_val1.month, calendar.monthrange(month_val1.year, month_val1.month)[1]))])

            out_move3_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                    ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                month_val2.year, month_val2.month, calendar.monthrange(month_val2.year, month_val2.month)[1]))])

            out_move4_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                    ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                month_val3.year, month_val3.month, calendar.monthrange(month_val3.year, month_val3.month)[1]))])

            # po search -----------------------------
            in_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val4.year, month_val4.month,
                                                                             calendar.monthrange(month_val4.year,
                                                                                                 month_val4.month)[1]))])
            in_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val0.year, month_val0.month, calendar.monthrange(month_val0.year, month_val0.month)[1]))])
            in_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val1.year, month_val1.month, calendar.monthrange(month_val1.year, month_val1.month)[1]))])
            in_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val2.year, month_val2.month, calendar.monthrange(month_val2.year, month_val2.month)[1]))])
            in_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val3.year, month_val3.month, calendar.monthrange(month_val3.year, month_val3.month)[1]))])

            for i, product in enumerate(product_id):
                to_stock = "No"
                to_order = "No"
                if product.route_ids.filtered(lambda l: l.name == "Manufacture"):
                    to_stock = "Yes"
                elif product.route_ids.filtered(lambda l: l.name == "Buy"):
                    to_order = "Yes"

                # so ----------------
                out_move1 = out_move1_all.filtered(lambda l: l.product_id == product)
                out_move2 = out_move2_all.filtered(lambda l: l.product_id == product)
                out_move3 = out_move3_all.filtered(lambda l: l.product_id == product)
                out_move4 = out_move4_all.filtered(lambda l: l.product_id == product)
                out_remain = out_remain_all.filtered(lambda l: l.product_id == product)
                out_before = out_before_all.filtered(lambda l: l.product_id == product)

                so_month4 = sum(out_move4.mapped("product_uom_qty"))
                so_month3 = sum(out_move3.mapped("product_uom_qty"))
                so_month2 = sum(out_move2.mapped("product_uom_qty"))
                so_month1 = sum(out_move1.mapped("product_uom_qty"))
                so_remain = sum(out_remain.mapped("product_uom_qty"))
                so_before = sum(out_before.mapped("product_uom_qty"))

                so_sum4month = sum([so_month1, so_month2, so_month3, so_month4])

                # so sold out state --------------------------
                out_move1_not_state = out_move1_all_not_state.filtered(lambda l: l.product_id == product)
                out_move2_not_state = out_move2_all_not_state.filtered(lambda l: l.product_id == product)
                out_move3_not_state = out_move3_all_not_state.filtered(lambda l: l.product_id == product)
                out_move4_not_state = out_move4_all_not_state.filtered(lambda l: l.product_id == product)

                so_month4_not_state = sum(out_move4_not_state.mapped("quantity"))
                so_month3_not_state = sum(out_move3_not_state.mapped("quantity"))
                so_month2_not_state = sum(out_move2_not_state.mapped("quantity"))
                so_month1_not_state = sum(out_move1_not_state.mapped("quantity"))

                # po ----------------
                in_move1 = in_move1_all.filtered(lambda l: l.product_id == product)
                in_move2 = in_move2_all.filtered(lambda l: l.product_id == product)
                in_move3 = in_move3_all.filtered(lambda l: l.product_id == product)
                in_move4 = in_move4_all.filtered(lambda l: l.product_id == product)
                in_before = in_before_all.filtered(lambda l: l.product_id == product)

                po_month4 = sum(in_move4.mapped("product_uom_qty"))
                po_month3 = sum(in_move3.mapped("product_uom_qty"))
                po_month2 = sum(in_move2.mapped("product_uom_qty"))
                po_month1 = sum(in_move1.mapped("product_uom_qty"))
                in_before = sum(in_before.mapped("product_uom_qty"))

                po_sum4month = sum([po_month1, po_month2, po_month3, po_month4])

                # AVG Sale per Month = ค่าเฉลี่ยยอดขายต่อเดือน (Q'ty SUM / 4)
                qty_sum_so = sum([so_month4_not_state, so_month3_not_state, so_month2_not_state, so_month1_not_state])
                avg_sale_per_m = (qty_sum_so/4)

                # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month

                if avg_sale_per_m == 0:
                    s_t = 0
                    s_t_b = 0
                else:
                    # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month
                    s_t = product.qty_available / avg_sale_per_m
                    # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
                    s_t_b = (product.qty_available + po_sum4month) / avg_sale_per_m

                # สั่งซื้อใหม่ = (AVG Sale per Month * จำนวนเดือนที่ต้องการสต็อค***)-(Stock+PO SUM)

                # จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ) = (PO SUM + Stock + สั่งซื้อใหม่)/AVG Sale per Month
                # month_sale = (po_sum4month + product.qty_available)

                i += 1
                data_list = [product.default_code or "",
                             product.name or "",
                             product.uom_id.name or "",
                             product.seller_ids[:1].name.name or "",
                             " ",
                             to_order,
                             to_stock,
                             product.seller_ids[:1].min_qty,
                             product.seller_ids[:1].product_uom.name or "",
                             so_before,
                             so_month4,
                             so_month3,
                             so_month2,
                             so_month1,
                             so_remain,
                             sum([so_sum4month, so_remain]),
                             in_before,
                             po_month4,
                             po_month3,
                             po_month2,
                             po_month1,
                             po_sum4month,
                             so_month4_not_state,
                             so_month3_not_state,
                             so_month2_not_state,
                             so_month1_not_state,
                             qty_sum_so,
                             avg_sale_per_m,
                             product.qty_available,
                             s_t,
                             s_t_b
                             ]
                sheet.write_row(i,0, data_list, data_cell_format)

        elif value.date_before == "six":
            for rec in range(39):
                sheet.set_column(0, rec, 15)

            sheet.write(0, 0, "Item number", head_cell_format)
            sheet.write(0, 1, "Product name", head_cell_format)
            sheet.write(0, 2, "Inventory unit", head_cell_format)
            sheet.write(0, 3, "Vendor", head_cell_format)
            sheet.write(0, 4, "Origin", head_cell_format)
            sheet.write(0, 5, "To Order", head_cell_format)
            sheet.write(0, 6, "To Stock", head_cell_format)
            sheet.write(0, 7, "Physical packing Qty", head_cell_format)
            sheet.write(0, 8, "Physical packing Unit", head_cell_format)
            sheet.write(0, 9, "สินค้าค้างส่งยกมา", head_cell_format)
            sheet.write(0, 10, "SO %s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 11, "SO %s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 12, "SO %s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 13, "SO %s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 14, "SO %s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 15, "SO %s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 16, "SO Remain", head_cell_format)
            sheet.write(0, 17, "SO SUM", head_cell_format)
            sheet.write(0, 18, "สินค้าค้างรับยกมา", head_cell_format)
            sheet.write(0, 19, "PO %s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 20, "PO %s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 21, "PO %s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 22, "PO %s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 23, "PO %s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 24, "PO %s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 25, "PO Total", head_cell_format)
            sheet.write(0, 26, "QTY.%s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 27, "QTY.%s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 28, "QTY.%s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 29, "QTY.%s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 30, "QTY.%s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 31, "QTY.%s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 32, "QTY.SUM", head_cell_format)
            sheet.write(0, 33, "Sale out/M", head_cell_format)
            sheet.write(0, 34, "STOCK", head_cell_format)
            sheet.write(0, 35, "จำนวนเดือนที่ขายได้(S/T)", head_cell_format)
            sheet.write(0, 36, "จำนวนเดือนที่ขายได้(S/T+B/O)", head_cell_format)
            sheet.write(0, 37, "สั่งซื้อใหม่", head_cell_format)
            sheet.write(0, 38, "จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ)", head_cell_format)

            product_id = self.env["product.product"].search([("type", "=", "product")])
            # for test one product
            # product_id = self.env["product.product"].search([("type", "=", "product"),("default_code", "=", "AABFBT42V042I4")])

            # so search --------------------------
            out_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            out_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val0.year, month_val0.month, calendar.monthrange(month_val0.year, month_val0.month)[1]))])
            out_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val1.year, month_val1.month, calendar.monthrange(month_val1.year, month_val1.month)[1]))])

            out_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val2.year, month_val2.month, calendar.monthrange(month_val2.year, month_val2.month)[1]))])

            out_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val3.year, month_val3.month, calendar.monthrange(month_val3.year, month_val3.month)[1]))])

            out_move5_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val4.year, month_val4.month,
                                                                             calendar.monthrange(month_val4.year,
                                                                                                 month_val4.month)[
                                                                                 1]))])

            out_move6_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val5.year, month_val5.month,
                                                                             calendar.monthrange(month_val5.year,
                                                                                                 month_val5.month)[
                                                                                 1]))])

            out_remain_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_remain.year, month_remain.month))])
            # so search not state --------------------------
            out_move1_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                    ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                month_val0.year, month_val0.month, calendar.monthrange(month_val0.year, month_val0.month)[1]))])
            out_move2_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val1.year, month_val1.month,
                                                                        calendar.monthrange(month_val1.year,
                                                                                            month_val1.month)[1]))])

            out_move3_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val2.year, month_val2.month,
                                                                        calendar.monthrange(month_val2.year,
                                                                                            month_val2.month)[1]))])

            out_move4_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val3.year, month_val3.month,
                                                                        calendar.monthrange(month_val3.year,
                                                                                            month_val3.month)[1]))])

            out_move5_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            out_move6_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val5.year, month_val5.month, calendar.monthrange(month_val5.year, month_val5.month)[1]))])

            # po search -----------------------------
            in_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                 month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            in_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val0.year, month_val0.month,
                                                                             calendar.monthrange(month_val0.year,
                                                                                                 month_val0.month)[
                                                                                 1]))])
            in_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val1.year, month_val1.month,
                                                                             calendar.monthrange(month_val1.year,
                                                                                                 month_val1.month)[
                                                                                 1]))])
            in_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val2.year, month_val2.month,
                                                                             calendar.monthrange(month_val2.year,
                                                                                                 month_val2.month)[
                                                                                 1]))])
            in_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val3.year, month_val3.month,
                                                                             calendar.monthrange(month_val3.year,
                                                                                                 month_val3.month)[
                                                                                 1]))])

            in_move5_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            in_move6_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val5.year, month_val5.month, calendar.monthrange(month_val5.year, month_val5.month)[1]))])

            for i, product in enumerate(product_id):
                to_stock = "No"
                to_order = "No"
                if product.route_ids.filtered(lambda l: l.name == "Manufacture"):
                    to_stock = "Yes"
                elif product.route_ids.filtered(lambda l: l.name == "Buy"):
                    to_order = "Yes"

                # so ----------------
                out_move1 = out_move1_all.filtered(lambda l: l.product_id == product)
                out_move2 = out_move2_all.filtered(lambda l: l.product_id == product)
                out_move3 = out_move3_all.filtered(lambda l: l.product_id == product)
                out_move4 = out_move4_all.filtered(lambda l: l.product_id == product)
                out_move5 = out_move5_all.filtered(lambda l: l.product_id == product)
                out_move6 = out_move6_all.filtered(lambda l: l.product_id == product)
                out_remain = out_remain_all.filtered(lambda l: l.product_id == product)
                out_before = out_before_all.filtered(lambda l: l.product_id == product)

                so_month6 = sum(out_move6.mapped("product_uom_qty"))
                so_month5 = sum(out_move5.mapped("product_uom_qty"))
                so_month4 = sum(out_move4.mapped("product_uom_qty"))
                so_month3 = sum(out_move3.mapped("product_uom_qty"))
                so_month2 = sum(out_move2.mapped("product_uom_qty"))
                so_month1 = sum(out_move1.mapped("product_uom_qty"))
                so_remain = sum(out_remain.mapped("product_uom_qty"))
                so_before = sum(out_before.mapped("product_uom_qty"))

                so_sum6month = sum([so_month1, so_month2, so_month3, so_month4,so_month5,so_month6])

                # so not state --------------------------
                out_move1_not_state = out_move1_all_not_state.filtered(lambda l: l.product_id == product)
                out_move2_not_state = out_move2_all_not_state.filtered(lambda l: l.product_id == product)
                out_move3_not_state = out_move3_all_not_state.filtered(lambda l: l.product_id == product)
                out_move4_not_state = out_move4_all_not_state.filtered(lambda l: l.product_id == product)
                out_move5_not_state = out_move5_all_not_state.filtered(lambda l: l.product_id == product)
                out_move6_not_state = out_move6_all_not_state.filtered(lambda l: l.product_id == product)

                so_month6_not_state = sum(out_move6_not_state.mapped("quantity"))
                so_month5_not_state = sum(out_move5_not_state.mapped("quantity"))
                so_month4_not_state = sum(out_move4_not_state.mapped("quantity"))
                so_month3_not_state = sum(out_move3_not_state.mapped("quantity"))
                so_month2_not_state = sum(out_move2_not_state.mapped("quantity"))
                so_month1_not_state = sum(out_move1_not_state.mapped("quantity"))

                # po ----------------
                in_move1 = in_move1_all.filtered(lambda l: l.product_id == product)
                in_move2 = in_move2_all.filtered(lambda l: l.product_id == product)
                in_move3 = in_move3_all.filtered(lambda l: l.product_id == product)
                in_move4 = in_move4_all.filtered(lambda l: l.product_id == product)
                in_move5 = in_move5_all.filtered(lambda l: l.product_id == product)
                in_move6 = in_move6_all.filtered(lambda l: l.product_id == product)
                in_before = in_before_all.filtered(lambda l: l.product_id == product)

                po_month6 = sum(in_move6.mapped("product_uom_qty"))
                po_month5 = sum(in_move5.mapped("product_uom_qty"))
                po_month4 = sum(in_move4.mapped("product_uom_qty"))
                po_month3 = sum(in_move3.mapped("product_uom_qty"))
                po_month2 = sum(in_move2.mapped("product_uom_qty"))
                po_month1 = sum(in_move1.mapped("product_uom_qty"))
                in_before = sum(in_before.mapped("product_uom_qty"))

                po_sum6month = sum([po_month1, po_month2, po_month3, po_month4, po_month5, po_month6])

                # AVG Sale per Month = ค่าเฉลี่ยยอดขายต่อเดือน (Q'ty SUM / 4)
                qty_sum_so = sum([so_month6_not_state,so_month5_not_state,so_month4_not_state, so_month3_not_state, so_month2_not_state, so_month1_not_state])
                avg_sale_per_m = (qty_sum_so/6)

                # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month

                if avg_sale_per_m == 0:
                    s_t = 0
                    s_t_b = 0
                else:
                    # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month
                    s_t = product.qty_available/avg_sale_per_m
                    # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
                    s_t_b = (product.qty_available + po_sum6month)/avg_sale_per_m

                # สั่งซื้อใหม่ = (AVG Sale per Month * จำนวนเดือนที่ต้องการสต็อค***)-(Stock+PO SUM)

                # จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ) = (PO SUM + Stock + สั่งซื้อใหม่)/AVG Sale per Month
                # month_sale = (po_sum6month + product.qty_available)

                i += 1
                data_list = [product.default_code or "", product.name or "", product.uom_id.name or "",
                             product.seller_ids[:1].name.name or "", " ", to_order, to_stock,
                             product.seller_ids[:1].min_qty, product.seller_ids[:1].product_uom.name or "",
                             so_before,
                             so_month6,
                             so_month5,
                             so_month4,
                             so_month3,
                             so_month2,
                             so_month1,
                             so_remain,
                             sum([so_sum6month, so_remain]),
                             in_before,
                             po_month6,po_month5,po_month4, po_month3, po_month2, po_month1, po_sum6month,
                             so_month6_not_state,
                             so_month5_not_state,
                             so_month4_not_state,
                             so_month3_not_state,
                             so_month2_not_state,
                             so_month1_not_state,
                             qty_sum_so,
                             avg_sale_per_m,
                             product.qty_available, s_t, s_t_b]
                sheet.write_row(i, 0, data_list, data_cell_format)

        else:
            for rec in range(57):
                sheet.set_column(0, rec, 15)

            sheet.write(0, 0, "Item number", head_cell_format)
            sheet.write(0, 1, "Product name", head_cell_format)
            sheet.write(0, 2, "Inventory unit", head_cell_format)
            sheet.write(0, 3, "Vendor", head_cell_format)
            sheet.write(0, 4, "Origin", head_cell_format)
            sheet.write(0, 5, "To Order", head_cell_format)
            sheet.write(0, 6, "To Stock", head_cell_format)
            sheet.write(0, 7, "Physical packing Qty", head_cell_format)
            sheet.write(0, 8, "Physical packing Unit", head_cell_format)
            sheet.write(0, 9, "สินค้าค้างส่งยกมา", head_cell_format)
            sheet.write(0, 10, "SO %s"%calendar.month_name[month_val11.month], head_cell_format)
            sheet.write(0, 11, "SO %s"%calendar.month_name[month_val10.month], head_cell_format)
            sheet.write(0, 12, "SO %s"%calendar.month_name[month_val9.month], head_cell_format)
            sheet.write(0, 13, "SO %s"%calendar.month_name[month_val8.month], head_cell_format)
            sheet.write(0, 14, "SO %s"%calendar.month_name[month_val7.month], head_cell_format)
            sheet.write(0, 15, "SO %s"%calendar.month_name[month_val6.month], head_cell_format)
            sheet.write(0, 16, "SO %s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 17, "SO %s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 18, "SO %s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 19, "SO %s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 20, "SO %s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 21, "SO %s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 22, "SO Remain", head_cell_format)
            sheet.write(0, 23, "SO SUM", head_cell_format)
            sheet.write(0, 24, "สินค้าค้างรับยกมา", head_cell_format)
            sheet.write(0, 25, "PO %s"%calendar.month_name[month_val11.month], head_cell_format)
            sheet.write(0, 26, "PO %s"%calendar.month_name[month_val10.month], head_cell_format)
            sheet.write(0, 27, "PO %s"%calendar.month_name[month_val9.month], head_cell_format)
            sheet.write(0, 28, "PO %s"%calendar.month_name[month_val8.month], head_cell_format)
            sheet.write(0, 29, "PO %s"%calendar.month_name[month_val7.month], head_cell_format)
            sheet.write(0, 30, "PO %s"%calendar.month_name[month_val6.month], head_cell_format)
            sheet.write(0, 31, "PO %s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 32, "PO %s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 33, "PO %s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 34, "PO %s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 35, "PO %s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 36, "PO %s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 37, "PO Total", head_cell_format)
            sheet.write(0, 38, "QTY.%s"%calendar.month_name[month_val11.month], head_cell_format)
            sheet.write(0, 39, "QTY.%s"%calendar.month_name[month_val10.month], head_cell_format)
            sheet.write(0, 40, "QTY.%s"%calendar.month_name[month_val9.month], head_cell_format)
            sheet.write(0, 41, "QTY.%s"%calendar.month_name[month_val8.month], head_cell_format)
            sheet.write(0, 42, "QTY.%s"%calendar.month_name[month_val7.month], head_cell_format)
            sheet.write(0, 43, "QTY.%s"%calendar.month_name[month_val6.month], head_cell_format)
            sheet.write(0, 44, "QTY.%s"%calendar.month_name[month_val5.month], head_cell_format)
            sheet.write(0, 45, "QTY.%s"%calendar.month_name[month_val4.month], head_cell_format)
            sheet.write(0, 46, "QTY.%s"%calendar.month_name[month_val3.month], head_cell_format)
            sheet.write(0, 47, "QTY.%s"%calendar.month_name[month_val2.month], head_cell_format)
            sheet.write(0, 48, "QTY.%s"%calendar.month_name[month_val1.month], head_cell_format)
            sheet.write(0, 49, "QTY.%s"%calendar.month_name[month_val0.month], head_cell_format)
            sheet.write(0, 50, "QTY.SUM", head_cell_format)
            sheet.write(0, 51, "Sale out/M", head_cell_format)
            sheet.write(0, 52, "STOCK", head_cell_format)
            sheet.write(0, 53, "จำนวนเดือนที่ขายได้(S/T)", head_cell_format)
            sheet.write(0, 54, "จำนวนเดือนที่ขายได้(S/T+B/O)", head_cell_format)
            sheet.write(0, 55, "สั่งซื้อใหม่", head_cell_format)
            sheet.write(0, 56, "จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ)", head_cell_format)

            product_id = self.env["product.product"].search([("type", "=", "product")])
            # for test one product
            # product_id = self.env["product.product"].search([("type", "=", "product"),("default_code", "=", "AABFBT42V042I4")])

            # so search --------------------------
            out_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])


            out_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val0.year, month_val0.month,
                                                                             calendar.monthrange(month_val0.year,
                                                                                                 month_val0.month)[
                                                                                 1]))])
            out_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val1.year, month_val1.month,
                                                                             calendar.monthrange(month_val1.year,
                                                                                                 month_val1.month)[
                                                                                 1]))])

            out_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val2.year, month_val2.month,
                                                                             calendar.monthrange(month_val2.year,
                                                                                                 month_val2.month)[
                                                                                 1]))])

            out_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val3.year, month_val3.month,
                                                                             calendar.monthrange(month_val3.year,
                                                                                                 month_val3.month)[
                                                                                 1]))])

            out_move5_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            out_move6_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val5.year, month_val5.month, calendar.monthrange(month_val5.year, month_val5.month)[1]))])

            out_move7_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val6.year, month_val6.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val6.year, month_val6.month,
                                                                             calendar.monthrange(month_val6.year,
                                                                                                 month_val6.month)[
                                                                                 1]))])
            out_move8_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val7.year, month_val7.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val7.year, month_val7.month,
                                                                             calendar.monthrange(month_val7.year,
                                                                                                 month_val7.month)[
                                                                                 1]))])
            out_move9_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val8.year, month_val8.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val8.year, month_val8.month,
                                                                             calendar.monthrange(month_val8.year,
                                                                                                 month_val8.month)[
                                                                                 1]))])
            out_move10_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val9.year, month_val9.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val9.year, month_val9.month,
                                                                             calendar.monthrange(month_val9.year,
                                                                                                 month_val9.month)[
                                                                                 1]))])
            out_move11_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val10.year, month_val10.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val10.year, month_val10.month,
                                                                             calendar.monthrange(month_val10.year,
                                                                                                 month_val10.month)[
                                                                                 1]))])
            out_move12_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val11.year, month_val11.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val11.year, month_val11.month,
                                                                             calendar.monthrange(month_val11.year,
                                                                                                 month_val11.month)[
                                                                                 1]))])
            out_remain_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_remain.year, month_remain.month))])
            # so search not state --------------------------
            out_move1_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val0.year, month_val0.month,
                                                                        calendar.monthrange(month_val0.year,
                                                                                            month_val0.month)[1]))])
            out_move2_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val1.year, month_val1.month, calendar.monthrange(month_val1.year, month_val1.month)[1]))])

            out_move3_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val2.year, month_val2.month, calendar.monthrange(month_val2.year, month_val2.month)[1]))])

            out_move4_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val3.year, month_val3.month, calendar.monthrange(month_val3.year, month_val3.month)[1]))])

            out_move5_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val4.year, month_val4.month,
                                                                        calendar.monthrange(month_val4.year,
                                                                                            month_val4.month)[1]))])

            out_move6_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(month_val5.year, month_val5.month,
                                                                        calendar.monthrange(month_val5.year,
                                                                                            month_val5.month)[1]))])

            out_move7_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val6.year, month_val6.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val6.year, month_val6.month, calendar.monthrange(month_val6.year, month_val6.month)[1]))])

            out_move8_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val7.year, month_val7.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val7.year, month_val7.month, calendar.monthrange(month_val7.year, month_val7.month)[1]))])

            out_move9_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val8.year, month_val8.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val8.year, month_val8.month, calendar.monthrange(month_val8.year, month_val8.month)[1]))])

            out_move10_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val9.year, month_val9.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val9.year, month_val9.month, calendar.monthrange(month_val9.year, month_val9.month)[1]))])

            out_move11_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val10.year, month_val10.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val10.year, month_val10.month, calendar.monthrange(month_val10.year, month_val10.month)[1]))])

            out_move12_all_not_state = self.env["account.move.line"].search(
                [("parent_state", "=", "posted"), ("move_id.move_type", "=", "out_invoice"),
                 ("move_id.invoice_date", ">=", "%s-%s-01 00:00:00"%(month_val11.year, month_val11.month)), (
                     "move_id.invoice_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val11.year, month_val11.month, calendar.monthrange(month_val11.year, month_val11.month)[1]))])
            # po search -----------------------------
            in_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                 month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            in_move1_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val0.year, month_val0.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val0.year, month_val0.month, calendar.monthrange(month_val0.year, month_val0.month)[1]))])
            in_move2_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val1.year, month_val1.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val1.year, month_val1.month, calendar.monthrange(month_val1.year, month_val1.month)[1]))])
            in_move3_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val2.year, month_val2.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val2.year, month_val2.month, calendar.monthrange(month_val2.year, month_val2.month)[1]))])
            in_move4_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val3.year, month_val3.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val3.year, month_val3.month, calendar.monthrange(month_val3.year, month_val3.month)[1]))])

            in_move5_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val4.year, month_val4.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val4.year, month_val4.month,
                                                                             calendar.monthrange(month_val4.year,
                                                                                                 month_val4.month)[
                                                                                 1]))])

            in_move6_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val5.year, month_val5.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(month_val5.year, month_val5.month,
                                                                             calendar.monthrange(month_val5.year,
                                                                                                 month_val5.month)[
                                                                                 1]))])
            in_move7_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val6.year, month_val6.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val6.year, month_val6.month, calendar.monthrange(month_val6.year, month_val6.month)[1]))])

            in_move8_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val7.year, month_val7.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val7.year, month_val7.month, calendar.monthrange(month_val7.year, month_val7.month)[1]))])

            in_move9_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val8.year, month_val8.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val8.year, month_val8.month, calendar.monthrange(month_val8.year, month_val8.month)[1]))])

            in_move10_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val9.year, month_val9.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val9.year, month_val9.month, calendar.monthrange(month_val9.year, month_val9.month)[1]))])

            in_move11_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val10.year, month_val10.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val10.year, month_val10.month, calendar.monthrange(month_val10.year, month_val10.month)[1]))])

            in_move12_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_val11.year, month_val11.month)), (
                     "picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val11.year, month_val11.month, calendar.monthrange(month_val11.year, month_val11.month)[1]))])

            for i, product in enumerate(product_id):
                to_stock = "No"
                to_order = "No"
                if product.route_ids.filtered(lambda l: l.name == "Manufacture"):
                    to_stock = "Yes"
                elif product.route_ids.filtered(lambda l: l.name == "Buy"):
                    to_order = "Yes"

                # so ----------------
                out_move1 = out_move1_all.filtered(lambda l: l.product_id == product)
                out_move2 = out_move2_all.filtered(lambda l: l.product_id == product)
                out_move3 = out_move3_all.filtered(lambda l: l.product_id == product)
                out_move4 = out_move4_all.filtered(lambda l: l.product_id == product)
                out_move5 = out_move5_all.filtered(lambda l: l.product_id == product)
                out_move6 = out_move6_all.filtered(lambda l: l.product_id == product)
                out_move7 = out_move7_all.filtered(lambda l: l.product_id == product)
                out_move8 = out_move8_all.filtered(lambda l: l.product_id == product)
                out_move9 = out_move9_all.filtered(lambda l: l.product_id == product)
                out_move10 = out_move10_all.filtered(lambda l: l.product_id == product)
                out_move11 = out_move11_all.filtered(lambda l: l.product_id == product)
                out_move12 = out_move12_all.filtered(lambda l: l.product_id == product)
                out_remain = out_remain_all.filtered(lambda l: l.product_id == product)
                out_before = out_before_all.filtered(lambda l: l.product_id == product)

                so_month12 = sum(out_move12.mapped("product_uom_qty"))
                so_month11 = sum(out_move11.mapped("product_uom_qty"))
                so_month10 = sum(out_move10.mapped("product_uom_qty"))
                so_month9 = sum(out_move9.mapped("product_uom_qty"))
                so_month8 = sum(out_move8.mapped("product_uom_qty"))
                so_month7 = sum(out_move7.mapped("product_uom_qty"))
                so_month6 = sum(out_move6.mapped("product_uom_qty"))
                so_month5 = sum(out_move5.mapped("product_uom_qty"))
                so_month4 = sum(out_move4.mapped("product_uom_qty"))
                so_month3 = sum(out_move3.mapped("product_uom_qty"))
                so_month2 = sum(out_move2.mapped("product_uom_qty"))
                so_month1 = sum(out_move1.mapped("product_uom_qty"))
                so_remain = sum(out_remain.mapped("product_uom_qty"))
                so_before = sum(out_before.mapped("product_uom_qty"))

                so_sum12month = sum([so_month1, so_month2, so_month3, so_month4, so_month5, so_month6,
                                    so_month7, so_month8, so_month9, so_month10, so_month11, so_month12])

                # so not state --------------------------
                out_move1_not_state = out_move1_all_not_state.filtered(lambda l: l.product_id == product)
                out_move2_not_state = out_move2_all_not_state.filtered(lambda l: l.product_id == product)
                out_move3_not_state = out_move3_all_not_state.filtered(lambda l: l.product_id == product)
                out_move4_not_state = out_move4_all_not_state.filtered(lambda l: l.product_id == product)
                out_move5_not_state = out_move5_all_not_state.filtered(lambda l: l.product_id == product)
                out_move6_not_state = out_move6_all_not_state.filtered(lambda l: l.product_id == product)
                out_move7_not_state = out_move7_all_not_state.filtered(lambda l: l.product_id == product)
                out_move8_not_state = out_move8_all_not_state.filtered(lambda l: l.product_id == product)
                out_move9_not_state = out_move9_all_not_state.filtered(lambda l: l.product_id == product)
                out_move10_not_state = out_move10_all_not_state.filtered(lambda l: l.product_id == product)
                out_move11_not_state = out_move11_all_not_state.filtered(lambda l: l.product_id == product)
                out_move12_not_state = out_move12_all_not_state.filtered(lambda l: l.product_id == product)

                so_month12_not_state = sum(out_move12_not_state.mapped("quantity"))
                so_month11_not_state = sum(out_move11_not_state.mapped("quantity"))
                so_month10_not_state = sum(out_move10_not_state.mapped("quantity"))
                so_month9_not_state = sum(out_move9_not_state.mapped("quantity"))
                so_month8_not_state = sum(out_move8_not_state.mapped("quantity"))
                so_month7_not_state = sum(out_move7_not_state.mapped("quantity"))
                so_month6_not_state = sum(out_move6_not_state.mapped("quantity"))
                so_month5_not_state = sum(out_move5_not_state.mapped("quantity"))
                so_month4_not_state = sum(out_move4_not_state.mapped("quantity"))
                so_month3_not_state = sum(out_move3_not_state.mapped("quantity"))
                so_month2_not_state = sum(out_move2_not_state.mapped("quantity"))
                so_month1_not_state = sum(out_move1_not_state.mapped("quantity"))

                # po ----------------
                in_move1 = in_move1_all.filtered(lambda l: l.product_id == product)
                in_move2 = in_move2_all.filtered(lambda l: l.product_id == product)
                in_move3 = in_move3_all.filtered(lambda l: l.product_id == product)
                in_move4 = in_move4_all.filtered(lambda l: l.product_id == product)
                in_move5 = in_move5_all.filtered(lambda l: l.product_id == product)
                in_move6 = in_move6_all.filtered(lambda l: l.product_id == product)
                in_move7 = in_move7_all.filtered(lambda l: l.product_id == product)
                in_move8 = in_move8_all.filtered(lambda l: l.product_id == product)
                in_move9 = in_move9_all.filtered(lambda l: l.product_id == product)
                in_move10 = in_move10_all.filtered(lambda l: l.product_id == product)
                in_move11 = in_move11_all.filtered(lambda l: l.product_id == product)
                in_move12 = in_move12_all.filtered(lambda l: l.product_id == product)
                in_before = in_before_all.filtered(lambda l: l.product_id == product)

                po_month12 = sum(in_move12.mapped("product_uom_qty"))
                po_month11 = sum(in_move11.mapped("product_uom_qty"))
                po_month10 = sum(in_move10.mapped("product_uom_qty"))
                po_month9 = sum(in_move9.mapped("product_uom_qty"))
                po_month8 = sum(in_move8.mapped("product_uom_qty"))
                po_month7 = sum(in_move7.mapped("product_uom_qty"))
                po_month6 = sum(in_move6.mapped("product_uom_qty"))
                po_month5 = sum(in_move5.mapped("product_uom_qty"))
                po_month4 = sum(in_move4.mapped("product_uom_qty"))
                po_month3 = sum(in_move3.mapped("product_uom_qty"))
                po_month2 = sum(in_move2.mapped("product_uom_qty"))
                po_month1 = sum(in_move1.mapped("product_uom_qty"))
                in_before = sum(in_before.mapped("product_uom_qty"))

                po_sum12month = sum([po_month1, po_month2, po_month3, po_month4, po_month5, po_month6,
                                    po_month7, po_month8, po_month9, po_month10, po_month11, po_month12])

                # AVG Sale per Month = ค่าเฉลี่ยยอดขายต่อเดือน (Q'ty SUM / 4)
                qty_sum_so = sum([so_month12_not_state,so_month11_not_state,so_month10_not_state,so_month9_not_state,so_month8_not_state,
                                  so_month7_not_state,so_month6_not_state,so_month5_not_state,so_month4_not_state, so_month3_not_state,
                                  so_month2_not_state, so_month1_not_state])
                avg_sale_per_m = (qty_sum_so/12)

                # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month

                if avg_sale_per_m == 0:
                    s_t = 0
                    s_t_b = 0
                else:
                    # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month
                    s_t = product.qty_available/avg_sale_per_m
                    # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
                    s_t_b = (product.qty_available + po_sum12month)/avg_sale_per_m

                # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
                if s_t == 0:
                    s_t_b = 0
                else:
                    s_t_b = (product.qty_available + po_sum12month)/s_t

                # สั่งซื้อใหม่ = (AVG Sale per Month * จำนวนเดือนที่ต้องการสต็อค***)-(Stock+PO SUM)

                # จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ) = (PO SUM + Stock + สั่งซื้อใหม่)/AVG Sale per Month
                # month_sale = (po_sum12month + product.qty_available)

                i += 1
                data_list = [product.default_code or "", product.name or "", product.uom_id.name or "",
                             product.seller_ids[:1].name.name or "", " ", to_order, to_stock,
                             product.seller_ids[:1].min_qty, product.seller_ids[:1].product_uom.name or "",
                             so_before, so_month12,so_month11,so_month10,so_month9,so_month8,so_month7,
                             so_month6,
                             so_month5,
                             so_month4,
                             so_month3,
                             so_month2, so_month1, so_remain,
                             sum([so_sum12month, so_remain]),
                             in_before,
                             po_month12, po_month11,po_month10,po_month9,po_month8,po_month7,
                             po_month6, po_month5, po_month4, po_month3,
                             po_month2, po_month1,
                             po_sum12month,
                             so_month12_not_state,so_month11_not_state,so_month10_not_state,so_month9_not_state,so_month8_not_state,so_month7_not_state,
                             so_month6_not_state, so_month5_not_state,
                             so_month4_not_state, so_month3_not_state, so_month2_not_state, so_month1_not_state,
                             qty_sum_so,
                             avg_sale_per_m,
                             product.qty_available,
                             s_t, s_t_b]
                sheet.write_row(i, 0, data_list, data_cell_format)


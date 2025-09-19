# -*- coding: utf-8 -*
import logging
from odoo import api, fields, models, _
from odoo.tools import populate
from datetime import date, datetime, timedelta
from lxml import etree, html
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    plan_partner_id = fields.Many2one("res.partner", string = "Vendor")
    plan_origin = fields.Char(string = "Origin")
    plan_to_order = fields.Char(string = "To Order", compute="_compute_plan_purchase")
    plan_to_stock = fields.Char(string = "To Stock", compute="_compute_plan_purchase")
    plan_packing_qty = fields.Float('Physical packing Qty', compute="_compute_plan_purchase")
    plan_packing_unit = fields.Many2one("uom.uom", string = "Physical packing Unit", compute="_compute_plan_purchase")
    plan_so_before = fields.Float('สินค้าค้างส่งยกมา', compute="_compute_plan_purchase")
    current_month_so = fields.Float(string = "Current Month SO", compute="_compute_plan_purchase")
    one_month_ago_so = fields.Float(string = "One Month Ago SO", compute="_compute_plan_purchase")
    two_months_ago_so = fields.Float(string = "Two Months Ago SO", compute="_compute_plan_purchase")
    three_months_ago_so = fields.Float(string = "Three Months Ago SO", compute="_compute_plan_purchase")
    so_remain = fields.Float('SO Remain', compute="_compute_plan_purchase")
    so_total = fields.Float('SO SUM', compute="_compute_plan_purchase")
    in_before = fields.Float('สินค้าค้างรับยกมา', compute="_compute_plan_purchase")
    current_month_po = fields.Float(string = "Current Month PO", compute="_compute_plan_purchase")
    one_month_ago_po = fields.Float(string = "One Month Ago PO", compute="_compute_plan_purchase")
    two_months_ago_po = fields.Float(string = "Two Months Ago PO", compute="_compute_plan_purchase")
    three_months_ago_po = fields.Float(string = "Three Months Ago PO", compute="_compute_plan_purchase")
    po_total = fields.Float('PO Total', compute="_compute_plan_purchase")
    current_month_qty = fields.Float(string = "Current Month QTY", compute="_compute_plan_purchase")
    one_month_ago_qty = fields.Float(string = "One Month Ago QTY", compute="_compute_plan_purchase")
    two_months_ago_qty = fields.Float(string = "Two Months Ago QTY", compute="_compute_plan_purchase")
    three_months_ago_qty = fields.Float(string = "Three Months Ago QTY", compute="_compute_plan_purchase")
    qty_total = fields.Float('QTY SUM', compute="_compute_plan_purchase")
    sale_out_total = fields.Float('Sale out/M', compute="_compute_plan_purchase")
    stock_total = fields.Float('STOCK', compute="_compute_plan_purchase")
    months_s_t = fields.Float('จำนวนเดือนที่ขายได้(S/T)', compute="_compute_plan_purchase")
    months_s_t_b_o = fields.Float('จำนวนเดือนที่ขายได้(S/T+B/O)', compute="_compute_plan_purchase")
    po_order = fields.Float('สั่งซื้อใหม่')
    months_s_t_b_o_po = fields.Float('จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ)')

    def _compute_plan_purchase(self):
        month_remain = date.today() + relativedelta(months = 1)
        month_val0 = date.today()
        month_val1 = date.today() - relativedelta(months = 1)
        month_val2 = date.today() - relativedelta(months = 2)
        month_val3 = date.today() - relativedelta(months = 3)
        month_val4 = date.today() - relativedelta(months = 4)

        for rec in self:
            to_stock = "No"
            to_order = "No"
            if rec.route_ids.filtered(lambda l: l.name == "Manufacture"):
                to_stock = "Yes"
            elif rec.route_ids.filtered(lambda l: l.name == "Buy"):
                to_order = "Yes"

            out_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                     month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

            out_before = out_before_all.filtered(lambda l: l.product_id == rec)
            so_before = sum(out_before.mapped("product_uom_qty"))

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

            out_remain_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                 ("picking_id.scheduled_date", ">=", "%s-%s-01 00:00:00"%(month_remain.year, month_remain.month))])

            out_move1 = out_move1_all.filtered(lambda l: l.product_id == rec)
            out_move2 = out_move2_all.filtered(lambda l: l.product_id == rec)
            out_move3 = out_move3_all.filtered(lambda l: l.product_id == rec)
            out_move4 = out_move4_all.filtered(lambda l: l.product_id == rec)
            out_remain = out_remain_all.filtered(lambda l: l.product_id == rec)

            so_month4 = sum(out_move4.mapped("product_uom_qty"))
            so_month3 = sum(out_move3.mapped("product_uom_qty"))
            so_month2 = sum(out_move2.mapped("product_uom_qty"))
            so_month1 = sum(out_move1.mapped("product_uom_qty"))
            so_remain = sum(out_remain.mapped("product_uom_qty"))
            so_sum4month = sum([so_month1, so_month2, so_month3, so_month4])

            in_before_all = self.env["stock.move"].search(
                [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "incoming"),
                 ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                 month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])
            in_before = in_before_all.filtered(lambda l: l.product_id == rec)
            in_before = sum(in_before.mapped("product_uom_qty"))

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

            in_move1 = in_move1_all.filtered(lambda l: l.product_id == rec)
            in_move2 = in_move2_all.filtered(lambda l: l.product_id == rec)
            in_move3 = in_move3_all.filtered(lambda l: l.product_id == rec)
            in_move4 = in_move4_all.filtered(lambda l: l.product_id == rec)

            po_month4 = sum(in_move4.mapped("product_uom_qty"))
            po_month3 = sum(in_move3.mapped("product_uom_qty"))
            po_month2 = sum(in_move2.mapped("product_uom_qty"))
            po_month1 = sum(in_move1.mapped("product_uom_qty"))
            po_sum4month = sum([po_month1, po_month2, po_month3, po_month4])

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

            out_move1_not_state = out_move1_all_not_state.filtered(lambda l: l.product_id == rec)
            out_move2_not_state = out_move2_all_not_state.filtered(lambda l: l.product_id == rec)
            out_move3_not_state = out_move3_all_not_state.filtered(lambda l: l.product_id == rec)
            out_move4_not_state = out_move4_all_not_state.filtered(lambda l: l.product_id == rec)

            so_month4_not_state = sum(out_move4_not_state.mapped("quantity"))
            so_month3_not_state = sum(out_move3_not_state.mapped("quantity"))
            so_month2_not_state = sum(out_move2_not_state.mapped("quantity"))
            so_month1_not_state = sum(out_move1_not_state.mapped("quantity"))

            qty_sum_so = sum([so_month4_not_state, so_month3_not_state, so_month2_not_state, so_month1_not_state])
            avg_sale_per_m = (qty_sum_so/4)

            if avg_sale_per_m == 0:
                s_t = 0
                s_t_b = 0
            else:
                # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month
                s_t = rec.qty_available/avg_sale_per_m
                # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
                s_t_b = (rec.qty_available + po_sum4month)/avg_sale_per_m

            rec.update({
                "plan_partner_id": rec.seller_ids[:1].name.id,
                "plan_to_order": to_order,
                "plan_to_stock": to_stock,
                "plan_packing_qty": rec.seller_ids[:1].min_qty,
                "plan_packing_unit": rec.seller_ids[:1].product_uom.id,
                "plan_so_before": so_before,
                "three_months_ago_so": so_month4,
                "two_months_ago_so": so_month3,
                "one_month_ago_so": so_month2,
                "current_month_so": so_month1,
                "so_remain": so_remain,
                "so_total": sum([so_sum4month, so_remain]),
                "in_before": in_before,
                "three_months_ago_po": po_month4,
                "two_months_ago_po": po_month3,
                "one_month_ago_po": po_month2,
                "current_month_po": po_month1,
                "po_total": po_sum4month,
                "three_months_ago_qty": so_month4_not_state,
                "two_months_ago_qty": so_month3_not_state,
                "one_month_ago_qty": so_month2_not_state,
                "current_month_qty": so_month1_not_state,
                "qty_total": qty_sum_so,
                "sale_out_total": avg_sale_per_m,
                "stock_total": rec.qty_available,
                "months_s_t": s_t,
                "months_s_t_b_o": s_t_b,
            })

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductProduct, self).fields_view_get(view_id = view_id, view_type = view_type, toolbar = toolbar, submenu = submenu)
        if view_type in ['form', 'tree', 'search']:
            doc = etree.XML(res['arch'])
            current_date = datetime.now()
            so_months = [("current_month_so", current_date.strftime('%B')),
                    ("one_month_ago_so", (current_date - timedelta(days = 30)).strftime('%B')),
                    ("two_months_ago_so", (current_date - timedelta(days = 60)).strftime('%B')),
                    ("three_months_ago_so", (current_date - timedelta(days = 90)).strftime('%B')),
                    ]
            po_months = [
                      ("current_month_po", current_date.strftime('%B')),
                      ("one_month_ago_po", (current_date - timedelta(days = 30)).strftime('%B')),
                      ("two_months_ago_po", (current_date - timedelta(days = 60)).strftime('%B')),
                      ("three_months_ago_po", (current_date - timedelta(days = 90)).strftime('%B')),
                      ]
            qty_months = [
                      ("current_month_qty", current_date.strftime('%B')),
                      ("one_month_ago_qty", (current_date - timedelta(days = 30)).strftime('%B')),
                      ("two_months_ago_qty", (current_date - timedelta(days = 60)).strftime('%B')),
                      ("three_months_ago_qty", (current_date - timedelta(days = 90)).strftime('%B')), ]
            for field_name, month in so_months:
                for node in doc.xpath(f"//field[@name='{field_name}']"):
                    node.set('string', f"SO {month}")
            for field_name, month in po_months:
                for node in doc.xpath(f"//field[@name='{field_name}']"):
                    node.set('string', f"PO {month}")
            for field_name, month in qty_months:
                for node in doc.xpath(f"//field[@name='{field_name}']"):
                    node.set('string', f"QTY {month}")
            res['arch'] = etree.tostring(doc, encoding = 'unicode')
        return res

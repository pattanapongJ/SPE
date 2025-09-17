# -*- coding: utf-8 -*
from odoo import api, fields, models, _
from odoo.tools import populate
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

class ProductProduct(models.Model):
    _inherit = "product.product"

    draft_rfq_total = fields.Float(string = "Auto Draft Rfq",compute="_compute_draft_rfq",default=0)
    draft_mrp_total = fields.Float(string = "Auto Draft MO",compute="_compute_draft_mrp",default=0)
    po_order = fields.Float('สั่งซื้อใหม่', compute="_compute_plan_purchase")

    def _compute_draft_rfq(self):
        for rec in self:
            purchase_line_ids = rec.env['purchase.order.line'].search([("product_id.id","=",rec.id),("product_qty", ">", 0)])
            total = 0
            for rec2 in purchase_line_ids:
                if rec2.order_id.state == 'draft':
                    total = total + rec2.product_qty
            rec.update({   
                 'draft_rfq_total': total,
                })   
    def _compute_draft_mrp(self):
        for rec in self:
            product_line_ids = rec.env['mr.product.list.line'].search([("product_id.id","=",rec.id),("demand_qty", ">", 0)])
            total = 0
            for rec2 in product_line_ids:
                if rec2.mr_id.state == 'draft':
                    total = total + rec2.demand_qty
            rec.update({   
                 'draft_mrp_total': total,
                })    
            
    def _compute_plan_purchase(self):
        for rec in self:
            res = rec.get_plan_purchase()
            rec.update(res)

    def get_plan_purchase(self):
        month_remain = date.today() + relativedelta(months = 1)
        month_val0 = date.today()
        month_val1 = date.today() - relativedelta(months = 1)
        month_val2 = date.today() - relativedelta(months = 2)
        month_val3 = date.today() - relativedelta(months = 3)
        month_val4 = date.today() - relativedelta(months = 4)

        to_stock = "No"
        to_order = "No"
        if self.route_ids.filtered(lambda l: l.name == "Manufacture"):
            to_stock = "Yes"
        elif self.route_ids.filtered(lambda l: l.name == "Buy"):
            to_order = "Yes"

        out_before_all = self.env["stock.move"].search(
            [("picking_id.state", "not in", ("done", "cancel")), ("picking_id.picking_type_code", "=", "outgoing"),
                ("picking_id.scheduled_date", "<=", "%s-%s-%s 23:59:59"%(
                    month_val4.year, month_val4.month, calendar.monthrange(month_val4.year, month_val4.month)[1]))])

        out_before = out_before_all.filtered(lambda l: l.product_id == self)
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

        out_move1 = out_move1_all.filtered(lambda l: l.product_id == self)
        out_move2 = out_move2_all.filtered(lambda l: l.product_id == self)
        out_move3 = out_move3_all.filtered(lambda l: l.product_id == self)
        out_move4 = out_move4_all.filtered(lambda l: l.product_id == self)
        out_remain = out_remain_all.filtered(lambda l: l.product_id == self)

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
        in_before = in_before_all.filtered(lambda l: l.product_id == self)
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

        in_move1 = in_move1_all.filtered(lambda l: l.product_id == self)
        in_move2 = in_move2_all.filtered(lambda l: l.product_id == self)
        in_move3 = in_move3_all.filtered(lambda l: l.product_id == self)
        in_move4 = in_move4_all.filtered(lambda l: l.product_id == self)

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

        out_move1_not_state = out_move1_all_not_state.filtered(lambda l: l.product_id == self)
        out_move2_not_state = out_move2_all_not_state.filtered(lambda l: l.product_id == self)
        out_move3_not_state = out_move3_all_not_state.filtered(lambda l: l.product_id == self)
        out_move4_not_state = out_move4_all_not_state.filtered(lambda l: l.product_id == self)

        so_month4_not_state = sum(out_move4_not_state.mapped("quantity"))
        so_month3_not_state = sum(out_move3_not_state.mapped("quantity"))
        so_month2_not_state = sum(out_move2_not_state.mapped("quantity"))
        so_month1_not_state = sum(out_move1_not_state.mapped("quantity"))

        qty_sum_so = sum([so_month4_not_state, so_month3_not_state, so_month2_not_state, so_month1_not_state])
        avg_sale_per_m = (qty_sum_so/4)

        sup_info_id = self.env["product.supplierinfo"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_id.id),
                ("name", "=", self.plan_partner_id.id),
            ])

        month_to_stock_product_id = False
        month_to_stock_product_tmpl_id = False
        if sup_info_id:
            if len(sup_info_id) > 1:
                for sup_info in sup_info_id:
                    if sup_info.product_id.id == self.id:
                        month_to_stock_product_id = sup_info.month_to_stock
                    elif sup_info.product_id.id == False:
                        month_to_stock_product_tmpl_id = sup_info.month_to_stock
            else:
                month_to_stock_product_tmpl_id = sup_info_id.month_to_stock
            if month_to_stock_product_id:
                month_to_stock = month_to_stock_product_id
            else:
                month_to_stock = month_to_stock_product_tmpl_id                        
        else:
            month_to_stock = 0

        # สั่งซื้อใหม่ = (AVG Sale per Month * จำนวนเดือนที่ต้องการสต็อค***)-(Stock+PO SUM)
        re_new = (avg_sale_per_m * month_to_stock)-(self.qty_available + po_sum4month)

        if avg_sale_per_m == 0:
            s_t = 0
            s_t_b = 0
            s_t_b_re_new = 0
        else:
            # จำนวนเดือนที่ขายได้(S/T) = Stock / AVG Sale per Month
            s_t = self.qty_available/avg_sale_per_m
            # จำนวนเดือนที่ขายได้(S/T+B/O) =  (Stock + PO Sum) / AVG Sale per Month
            s_t_b = (self.qty_available + po_sum4month)/avg_sale_per_m
            # จำนวนเดือนที่ขายได้(S/T+B/O+สั่งซื้อ) = (PO SUM + Stock + สั่งซื้อใหม่)/AVG Sale per Month
            s_t_b_re_new = (po_sum4month + self.qty_available + re_new)/avg_sale_per_m

        plan_forecast = {"plan_partner_id": self.seller_ids[:1].name.id,
                "plan_to_order": to_order,
                "plan_to_stock": to_stock,
                "plan_packing_qty": self.seller_ids[:1].min_qty,
                "plan_packing_unit": self.seller_ids[:1].product_uom.id,
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
                "stock_total": self.qty_available,
                "months_s_t": s_t,
                "months_s_t_b_o": s_t_b,
                "po_order":re_new,
                "months_s_t_b_o_po":s_t_b_re_new,}
        
        return plan_forecast
        
    def create_rfq_auto(self,po_order):
        order_line = []
        purchase_model = self.env['purchase.order']
        partner_id_auto = self.env['res.partner'].search([("name","=",'Auto Create')])
        line = (0, 0, {
                    'product_id': self.id,
                    'name': self.display_name,
                    'product_qty': po_order, #set new qty
                    'product_uom': self.uom_id.id,
                })
        order_line.append(line)
        purchase_id = purchase_model.create({
            'name': 'New',
            'partner_id': partner_id_auto.id,
            'order_line': order_line
        })
    
    def create_mr_auto(self,po_order):
        order_line = []
        mrp_request_model = self.env['mrp.mr']
        partner_id_auto = self.env['res.partner'].search([("name","=",'Auto Create')])
        request_type_id_auto = self.env['request.type.mr'].search([("name","=",'สินค้าเคยมีการสั่งผลิต')])
        line = (0, 0, {
                    'product_id': self.id,
                    'demand_qty': po_order, #set new qty
                    'uom_id': self.uom_id.id,
                })
        order_line.append(line)
        if self.product_type_mr:
            mrp_request_id = mrp_request_model.create({
                'name': 'New',
                'partner_id': partner_id_auto.id,
                'request_type':request_type_id_auto.id,
                'product_line_ids': order_line,
                'product_type':self.product_type_mr.id,
                'department_id': self.product_type_mr.department_id.id,
                'delivery_method':"m2c",
            })

    def create_record_auto(self):
        product_ids = self.env['product.product'].search([])
        number = 0
        for rec in product_ids:
            number += 1
            plan_forecast = rec.get_plan_purchase()
            po_order = plan_forecast.get("po_order")
            plan_to_order = plan_forecast.get("plan_to_order")
            plan_to_stock = plan_forecast.get("plan_to_stock")
            if po_order > 0:
                if plan_to_order == "Yes":
                    rec.create_rfq_auto(po_order)
                elif plan_to_stock == "Yes":
                    rec.create_mr_auto(po_order)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_type_mr = fields.Many2one('product.type.mr', string='Product Type MRP', tracking=True,index=True,)
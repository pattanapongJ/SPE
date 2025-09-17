# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class FinancialDetailSummaryView(models.TransientModel):
    _name = "financial.detail.summary.view"
    _description = "Financial Detail View"
    _order = "date"

    product_id = fields.Many2one(comodel_name="product.product")
    default_code = fields.Char(string="Internal Reference")
    product_uom_id = fields.Many2one('uom.uom', 'Unit', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    amount_qty = fields.Float(string="ยอดคงเหลือ")
    amount_unit_price = fields.Float(string="ราคา-หน่วย")
    amount_price = fields.Float(string="มูลค่า")
    qty_in = fields.Float(string="รับเข้า")
    in_unit_price = fields.Float(string="ราคา-หน่วย")
    in_price = fields.Float(string="มูลค่า")
    qty_out = fields.Float(string="จ่ายออก")
    out_unit_price = fields.Float(string="ราคา-หน่วย")
    out_price = fields.Float(string="มูลค่า")
    qty_available = fields.Float(string="จำนวนคงเหลือก่อนวันเริ่มต้น")
    location_dest_id = fields.Many2one('stock.location', 'Location', check_company=True, required=True)

class FinancialDetailReportSummary(models.TransientModel):
    _name = "report.financial.detail.report.summary"
    _description = "Financial Detail Report Summary"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_id = fields.Many2many('product.product', string='สินค้า')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    # location_id = fields.Many2one('stock.location', string = 'Location')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string = 'Location')

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="financial.detail.summary.view",
        compute="_compute_results",
    )

    def _compute_results(self):
        self.ensure_one()
        
        if self.product_id:
            product_id = self.env['product.product'].search([('id', '=', self.product_id.ids), ('type', '!=', 'service')])
        else:
            product_id = self.env['product.product'].search([('type', '!=', 'service'),('write_date', '<=', self.date_to), ('write_date', '>=', self.date_from)])

        financial_detail_results = []
        
        for i, product_ids in enumerate(product_id):
            financial_detail_results_product = []
            financial_detail_results_location = []
            before_total = 0
            amount_before = 0
            amount_qty = 0
            qty_9 = 0
            qty_11 = 0
            in_unit_price  = 0
            in_price = 0
            out_unit_price = 0
            out_price = 0
            qty_available = 0

            if self.location_ids:
                stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('location_id', 'in',self.location_ids.ids),('location_id.usage', 'in',('internal', 'transit'))])
                        
            else:
                if self.warehouse_ids:
                    stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('warehouse_id', 'in',self.warehouse_ids.ids),('location_id.usage', 'in',('internal', 'transit'))])

                else:
                    stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', product_ids.id),('location_id.usage', 'in',('internal', 'transit'))])
            for sq in stock_quant:
                if sq.location_id.id not in financial_detail_results_location:
                    financial_detail_results_location.append(sq.location_id.id)
            
            if self.date_to and self.date_from:
                stock_move_id = self.env['stock.move.line'].search(
                            [('date', '<=', self.date_to), ('date', '>=', self.date_from), ('state', '=', 'done'),
                            ('product_id', '=', product_ids.id)], order="date")
                if self.location_ids:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', self.date_from), ('product_id', '=', product_ids.id),('location_id', 'in', self.location_ids.ids)])

                else:
                    if self.warehouse_ids:
                        stock_quant = self.env['stock.quant'].search(
                        [('create_date', '<', self.date_from), ('product_id', '=', product_ids.id), ('warehouse_id', 'in', self.warehouse_ids.ids),('location_id.usage', 'in', ('internal', 'transit'))])

                    else:
                        stock_quant = self.env['stock.quant'].search(
                        [('create_date', '<', self.date_from), ('product_id', '=', product_ids.id),('location_id.usage', 'in', ('internal', 'transit'))])
            else:
                stock_move_id = self.env['stock.move.line'].search(
                            [('state', '=', 'done'), ('product_id', '=', product_ids.id),], order="date")
                
            if stock_move_id:
                if stock_quant:
                    for before_stock_quant_ids in stock_quant:
                        amount_before += before_stock_quant_ids.quantity
                
                qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from)
                if self.location_ids:
                    qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from,warehouse_id=self.warehouse_ids,location_id=self.location_ids)
                else:
                    if self.warehouse_ids:
                        qty_available = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from,warehouse_id=self.warehouse_ids)

                before_total = before_total + amount_before
                amount_qty = qty_available
                for stock_move_ids in stock_move_id:
                    stock_move_line_ids = stock_move_ids
                    sale_price = stock_move_line_ids.sale_price 
                    origin = stock_move_line_ids.origin                   
                    customer = ""
                    purchase_order = None
                    if origin:
                        sale_order = self.env['sale.order'].search(
                         [('name', '=', origin)])
                        purchase_order = self.env['purchase.order'].search(
                         [('name', '=', origin)])
                        rma_order = self.env['crm.claim.ept'].search(
                         [('code', '=', origin)])
                        if sale_order:
                            customer = sale_order.partner_id.name
                        elif purchase_order:
                            customer = purchase_order.partner_id.name
                        elif rma_order:
                            customer = rma_order.partner_id.name

                    invoice = stock_move_line_ids.picking_id.invoice_ids
                    invoice_posted = invoice.search([('state', '=', 'posted'),('id','in',invoice.ids)])

                    if len(invoice_posted) > 1:
                        last_date = invoice_posted[0].write_date
                        inv_last = invoice_posted[0]
                        for inv in invoice_posted:
                            if inv.write_date > last_date:
                                inv_last = inv
                        invoice_posted = inv_last

                    qty = stock_move_line_ids.product_uom_id._compute_quantity(stock_move_line_ids.qty_done, stock_move_line_ids.product_id.uom_id)
                    if purchase_order:
                        purchase_order_line = self.env['purchase.order.line'].search([('order_id', '=', purchase_order.id),('product_id','=',product_ids.id)])
                        if purchase_order_line:
                            unit_price = purchase_order_line[-1].price_unit
                        else:
                            unit_price = stock_move_line_ids.move_id.price_unit
                    else:
                        unit_price = stock_move_line_ids.product_id.standard_price

                    location_id_check = False
                    location_dest_id_check = False
                    if self.location_ids:
                        if stock_move_line_ids.location_id.id in self.location_ids.ids:
                            location_id_check = True
                        if stock_move_line_ids.location_dest_id.id in self.location_ids.ids:
                            location_dest_id_check = True
                    elif self.warehouse_ids:
                        if stock_move_line_ids.location_id.warehouse_id.id in self.warehouse_ids.ids:
                            location_id_check = True
                        if stock_move_line_ids.location_dest_id.warehouse_id.id in self.warehouse_ids.ids:
                            location_dest_id_check = True
                    else:
                        location_id_check = True
                        location_dest_id_check = True
                    
                    if stock_move_ids.location_id.usage in ('internal', 'transit') and location_id_check:
                        amount_qty = amount_qty - qty
                        qty_9 = False
                        in_unit_price = False
                        in_price = False
                        qty_11 = qty
                        out_unit_price = unit_price
                        out_price = qty * unit_price

                        amount_price = amount_qty * product_ids.standard_price

                        data_list = {
                        "product_id":product_ids.id,
                        "location_dest_id":stock_move_line_ids.location_id.id,
                        "qty_in":qty_9,
                        "in_unit_price":in_unit_price,
                        "in_price":in_price,
                        "qty_out":qty_11,
                        "out_unit_price":out_unit_price,
                        "out_price":out_price,
                        "amount_qty":amount_qty,
                        "amount_unit_price":product_ids.standard_price,
                        "amount_price":amount_price,
                        "qty_available":qty_available,
                        }
                        financial_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_id.id not in financial_detail_results_location:
                            financial_detail_results_location.append(stock_move_line_ids.location_id.id)
                    
                    if stock_move_ids.location_dest_id.usage in ('internal', 'transit') and location_dest_id_check:
                        amount_qty = amount_qty + qty
                        qty_9 = qty
                        in_unit_price = unit_price
                        in_price = qty * unit_price
                        qty_11 = False
                        out_unit_price = False
                        out_price = False

                        amount_price = amount_qty * product_ids.standard_price

                        data_list = {
                            "product_id":product_ids.id,
                            "location_dest_id":stock_move_line_ids.location_dest_id.id,
                            "qty_in":qty_9,
                            "in_unit_price":in_unit_price,
                            "in_price":in_price,
                            "qty_out":qty_11,
                            "out_unit_price":out_unit_price,
                            "out_price":out_price,
                            "amount_qty":amount_qty,
                            "amount_unit_price":product_ids.standard_price,
                            "amount_price":amount_price,
                            "qty_available":qty_available,
                        }
                        financial_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_dest_id.id not in financial_detail_results_location:
                            financial_detail_results_location.append(stock_move_line_ids.location_dest_id.id)

                    in_unit_price  = False
                    out_unit_price = False
            
                for locat in financial_detail_results_location:
                    qty_in_summary = 0
                    in_price_summary = 0
                    qty_out_summary = 0
                    out_price_summary = 0
                    amount_qty_summary = 0
                    amount_price_summary = 0
                    qty_available_summary = 0
                    for data in financial_detail_results_product:
                        if data["location_dest_id"] == locat:
                            qty_in_summary = qty_in_summary + data["qty_in"]
                            in_price_summary = in_price_summary + data["in_price"]
                            qty_out_summary = qty_out_summary + data["qty_out"]
                            out_price_summary = out_price_summary + data["out_price"]           

                    location_summary = self.env['stock.location'].search([('id', '=', locat)])
                    qty_available_summary = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from,warehouse_id=location_summary.warehouse_id,location_id=location_summary)
                    amount_qty_summary = qty_available_summary + qty_in_summary - qty_out_summary
                    amount_price_summary = amount_qty_summary * product_ids.standard_price

                    in_unit_price = 0
                    out_unit_price = 0
                    if qty_in_summary > 0:
                        in_unit_price = in_price_summary / qty_in_summary
                    if qty_out_summary > 0:
                        out_unit_price = out_price_summary / qty_out_summary
                    data_list = {
                            "product_id":product_ids.id,
                            "default_code":product_ids.default_code,
                            "product_uom_id":product_ids.uom_id.id,
                            "location_dest_id":locat,
                            "qty_in":qty_in_summary,
                            "in_unit_price":in_unit_price,
                            "in_price":in_price_summary,
                            "qty_out":qty_out_summary,
                            "out_unit_price":out_unit_price,
                            "out_price":out_price_summary,
                            "amount_qty":amount_qty_summary,
                            "amount_unit_price":product_ids.standard_price,
                            "amount_price":amount_price_summary,
                            "qty_available":qty_available_summary,
                    }
                    financial_detail_results.append(data_list)    

        ReportLine = self.env["financial.detail.summary.view"]
        self.results = [ReportLine.new(line).id for line in financial_detail_results]
        
    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env['ir.actions.report'].search(
            [('report_name', '=', 'financial_detail_report_summary_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1))
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "hdc_stock_card_report.report_financial_detail_report_summary_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

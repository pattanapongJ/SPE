# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _,api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class PhysicalDetailSummaryView(models.TransientModel):
    _name = "physical.detail.summary.view"
    _description = "Physical Detail Summary View"
    _order = "date"

    product_id = fields.Many2one(comodel_name="product.product")
    default_code = fields.Char(string="Internal Reference")
    product_uom_id = fields.Many2one('uom.uom', 'Unit', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    amount_qty = fields.Float(string="ยอดคงเหลือ")
    qty_in = fields.Float(string="รับเข้า")
    qty_out = fields.Float(string="จ่ายออก")
    qty_available = fields.Float(string="จำนวนคงเหลือก่อนวันเริ่มต้น")
    location_dest_id = fields.Many2one('stock.location', 'Location', check_company=True, required=True)

class PhysicalDetailReportSummary(models.TransientModel):
    _name = "report.physical.detail.report.summary"
    _description = "Physical Detail Report Summary "

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_id = fields.Many2many('product.product', string='สินค้า')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    # location_id = fields.Many2one('stock.location', string = 'Location')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string = 'Location',domain="[('warehouse_id', 'in', warehouse_ids)]",)

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="physical.detail.summary.view",
        compute="_compute_results",
    )
    
    def _compute_results(self):
        self.ensure_one()
        
        if self.product_id:
            product_id = self.env['product.product'].search([('id', '=', self.product_id.ids), ('type', '!=', 'service')])
        else:
            product_id = self.env['product.product'].search([('type', '!=', 'service'),('write_date', '<=', self.date_to), ('write_date', '>=', self.date_from)])

        physical_detail_results = []

        for i, product_ids in enumerate(product_id):
            physical_detail_results_product = []
            physical_detail_results_location = []
            before_total = 0
            amount_before = 0
            amount_qty = 0
            qty_9 = 0
            qty_11 = 0
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
                if sq.location_id.id not in physical_detail_results_location:
                    physical_detail_results_location.append(sq.location_id.id)
            
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
                    origin = stock_move_line_ids.origin                   
                    customer = ""
                    if origin:
                        sale_order = self.env['sale.order'].search(
                         [('name', '=', origin)])
                        purchase_order = self.env['purchase.order'].search(
                         [('name', '=', origin)])
                        if sale_order:
                            customer = sale_order.partner_id.name
                        elif purchase_order:
                            customer = purchase_order.partner_id.name

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
                        qty_11 = qty

                        data_list = {
                            "product_id":product_ids.id,
                            "location_dest_id":stock_move_line_ids.location_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_id.id not in physical_detail_results_location:
                                    physical_detail_results_location.append(stock_move_line_ids.location_id.id)
                            
                    if stock_move_ids.location_dest_id.usage in ('internal', 'transit') and location_dest_id_check:
                        amount_qty = amount_qty + qty
                        qty_9 = qty
                        qty_11 = False

                        data_list = {
                            "product_id":product_ids.id,
                            "location_dest_id":stock_move_line_ids.location_dest_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results_product.append(data_list)
                        if stock_move_line_ids.location_dest_id.id not in physical_detail_results_location:
                                    physical_detail_results_location.append(stock_move_line_ids.location_dest_id.id)
            
            for locat in physical_detail_results_location:
                qty_in_summary = 0
                qty_out_summary = 0
                amount_qty_summary = 0
                qty_available_summary = 0
                for data in physical_detail_results_product:
                    if data["location_dest_id"] == locat:
                        qty_in_summary = qty_in_summary + data["qty_in"]
                        qty_out_summary = qty_out_summary + data["qty_out"]        

                location_summary = self.env['stock.location'].search([('id', '=', locat)])
                qty_available_summary = product_ids._compute_quantities_dict_warehouse_location_lot(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from,warehouse_id=location_summary.warehouse_id,location_id=location_summary)
                amount_qty_summary = qty_available_summary + qty_in_summary - qty_out_summary

                data_list = {
                            "product_id":product_ids.id,
                            "default_code":product_ids.default_code,
                            "product_uom_id":product_ids.uom_id.id,
                            "location_dest_id":locat,
                            "amount_qty":amount_qty_summary,
                            "qty_in":qty_in_summary,
                            "qty_out":qty_out_summary,
                            "qty_available":qty_available_summary,
                        }
                physical_detail_results.append(data_list)    
                    
        ReportLine = self.env["physical.detail.summary.view"]
        self.results = [ReportLine.new(line).id for line in physical_detail_results]

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env['ir.actions.report'].search(
            [('report_name', '=', 'physical_detail_report_summary_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1))
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "hdc_stock_card_report.report_physical_detail_report_summary_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

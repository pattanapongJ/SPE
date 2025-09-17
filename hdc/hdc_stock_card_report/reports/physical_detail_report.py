# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _,api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class PhysicalDetailView(models.TransientModel):
    _name = "physical.detail.view"
    _description = "Physical Detail View"
    _order = "date"

    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name="product.product")
    default_code = fields.Char(string="Internal Reference")
    origin = fields.Char(string="Source.No.")
    reference = fields.Char(string="REF.No.")
    reference_detail = fields.Char(string="รายละเอียดของ REF.No.")
    customer = fields.Char(string="CustVendAccount")
    invoice_name = fields.Char(string="SPE Invoice")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    product_uom_id = fields.Many2one('uom.uom', 'Unit', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    location_dest_id = fields.Many2one('stock.location', 'Location', check_company=True, required=True)
    amount_qty = fields.Float(string="ยอดคงเหลือ")
    qty_in = fields.Float(string="รับเข้า")
    qty_out = fields.Float(string="จ่ายออก")
    qty_available = fields.Float(string="จำนวนคงเหลือก่อนวันเริ่มต้น")

class PhysicalDetailReport(models.TransientModel):
    _name = "report.physical.detail.report"
    _description = "Physical Detail Report"

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
        comodel_name="physical.detail.view",
        compute="_compute_results",
    )
    def get_reference_detail(self,reference=False):
        operation_type={
            "OUTC24ITT":"Delivery Order Inter Transfer",
            "OUTCFAC1ITT":"Delivery Order Inter Transfer",
            "OUTCGIITT":"Delivery Order Inter Transfer",
            "OUTCLLKITT":"Delivery Order Inter Transfer",
            "OUTCNPTITT":"Delivery Order Inter Transfer",
            "OUTCRETITT":"Delivery Order Inter Transfer",
            "OUTFAC3ITT":"Delivery Order Inter Transfer", 
            "INCFAC3ITT":"Receipt Order Inter Transfer",
            "INCFACITT":"Receipt Order Inter Transfer",
            "INCGIITT":"Receipt Order Inter Transfer",
            "INCLLKITT":"Receipt Order Inter Transfer",
            "INCNPTITT":"Receipt Order Inter Transfer",
            "INCRETITT":"Receipt Order Inter Transfer",
            "C24BINITT":"Receipt Order Inter Transfer",
            "C24BOUTITT":"Delivery Order Inter Transfer",
            "C24BRC":"Return Customer",
            "C24INITT":"Receipt Order Inter Transfer",
            "C24RC":"Return Customer",
            "CFAC3ITT":"C-FAC3 Inter Transfer",
            "CFACITT":"C-FAC1 Inter Transfer",
            "CGIITT":"C-GI Inter Transfer",
            "CGIRC":"Return Customer",
            "CLLITT":"CLLK Inter Transfer",
            "CLLKRC":"Return Customer",
            "CNPTITT":"C-NPT Inter Transfer",
            "CRETITT":"C-RET Inter Transfer",
            "FAC1RC":"Return Customer",
            "FAC3RC":"Return Customer",
            "NPTRC":"Return Customer",
            "RETRC":"Return Customer",
            "BF":"การเบิกสินค้า (ของแถม)",
            "BRS":"การเบิก/ยืมสินค้าภายในเครื่องมือ",
            "IN":"Receipts",
            "INT":"Internal Transfers",
            "ITT":"Inter Transfer",
            "MO":"Manufacturing",
            "OUT":"Delivery Orders",    
            "RB":"การคืนสินค้า จากการยืม",
            }
        operation_type_code = list(operation_type.keys())
        for code in operation_type_code:
            if "/"+code+"/" in reference:
                return operation_type.get(code)
        return ""
    
    def _compute_results(self):
        self.ensure_one()
        
        if self.product_id:
            product_id = self.env['product.product'].search([('id', '=', self.product_id.ids), ('type', '!=', 'service')])
        else:
            product_id = self.env['product.product'].search([('type', '!=', 'service'),('write_date', '<=', self.date_to), ('write_date', '>=', self.date_from)])

        physical_detail_results = []

        for i, product_ids in enumerate(product_id):
            before_total = 0
            amount_before = 0
            amount_qty = 0
            qty_9 = None
            qty_11 = None
            qty_available = None
            
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
                            "date":stock_move_ids.date,
                            "product_id":product_ids.id,
                            "default_code":product_ids.default_code,
                            "reference":stock_move_line_ids.reference,
                            "origin":origin ,
                            "reference_detail":self.get_reference_detail(stock_move_line_ids.reference),
                            "customer":customer,
                            "invoice_name":invoice_posted.name,
                            "company_id":stock_move_line_ids.company_id.id,
                            "product_uom_id":stock_move_line_ids.product_uom_id.id,
                            "location_dest_id":stock_move_line_ids.location_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results.append(data_list)
                    if stock_move_ids.location_dest_id.usage in ('internal', 'transit') and location_dest_id_check:
                        amount_qty = amount_qty + qty
                        qty_9 = qty
                        qty_11 = False

                        data_list = {
                            "date":stock_move_ids.date,
                            "product_id":product_ids.id,
                            "default_code":product_ids.default_code,
                            "reference":stock_move_line_ids.reference,
                            "origin":origin ,
                            "reference_detail":self.get_reference_detail(stock_move_line_ids.reference),
                            "customer":customer,
                            "invoice_name":invoice_posted.name,
                            "company_id":stock_move_line_ids.company_id.id,
                            "product_uom_id":stock_move_line_ids.product_uom_id.id,
                            "location_dest_id":stock_move_line_ids.location_dest_id.id,
                            "amount_qty":amount_qty,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "qty_available":qty_available,
                        }
                        physical_detail_results.append(data_list)
                    
        ReportLine = self.env["physical.detail.view"]
        self.results = [ReportLine.new(line).id for line in physical_detail_results]

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env['ir.actions.report'].search(
            [('report_name', '=', 'physical_detail_report_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1))
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "hdc_stock_card_report.report_physical_detail_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

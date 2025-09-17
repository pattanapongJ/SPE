# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMovementView(models.TransientModel):
    _name = "stock.movement.view"
    _description = "Stock Movement View"
    _order = "date"

    warehouse_id = fields.Many2one('stock.warehouse', string='WH')
    pd_type_name = fields.Char(string="Product Type")
    categ_id = fields.Many2one(comodel_name="product.category",string="Product Category")
    origin = fields.Char(string="เลขที่เอกสาร")
    reference = fields.Char(string="เลขที่ออเดอร์")
    date = fields.Datetime(string="วันนำเข้า ออก")
    default_code = fields.Char(string="รหัสสินค้า")
    product_id = fields.Many2one(comodel_name="product.product")
    cost_unit_price = fields.Float(string="Cost(THB/Unit)") 
    qty_in = fields.Float(string="นำเข้า")
    qty_out = fields.Float(string="เบิกออก")
    amount_qty = fields.Float(string="คงเหลือ")
    product_uom_id = fields.Many2one('uom.uom', 'หน่วยนับ', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    qty_available = fields.Float(string="จำนวนคงเหลือก่อนวันเริ่มต้น")
    

class StockMovementReport(models.TransientModel):
    _name = "report.stock.movement.report"
    _description = "Stock Movement Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_id = fields.Many2many('product.product', string='สินค้า')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    before_total_sum = fields.Float()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.movement.view",
        compute="_compute_results",
    )

    def get_selection(self,pd_type):
        # for record in self:
        stored_value = pd_type
        if stored_value is None or stored_value is False:
            display_value = ''
        else:
            selection_list = self.env["product.template"]._fields["type"].selection
            selection_dict = dict(selection_list)
            display_value = selection_dict.get(stored_value, '')

        return display_value

    def _compute_results(self):
        self.ensure_one()
        
        if self.product_id:
            product_id = self.env['product.product'].search([('id', '=', self.product_id.ids), ('type', '!=', 'service')])
        else:
            product_id = self.env['product.product'].search([('type', '!=', 'service'),('write_date', '<=', self.date_to), ('write_date', '>=', self.date_from)])

        stock_movement_results = []        
        before_total_sum = 0

        for i, product_ids in enumerate(product_id):
            before_total = 0
            amount_qty = 0
            amount_before = 0
            qty_9 = None
            qty_11 = None
            pd_type_name = ""
            qty_available = None

            if self.date_to and self.date_from:

                if self.warehouse_ids:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', self.date_from), ('product_id', '=', product_ids.id), ('warehouse_id', 'in', self.warehouse_ids.ids),('location_id.usage', 'in', ('internal', 'transit'))])

                    stock_move_id = self.env['stock.move'].search(
                    [('date', '<=', self.date_to), ('date', '>=', self.date_from), ('state', '=', 'done'), ('warehouse_id', 'in', self.warehouse_ids.ids),
                     ('product_id', '=', product_ids.id)], order="date")

                else:
                    stock_quant = self.env['stock.quant'].search(
                    [('create_date', '<', self.date_from), ('product_id', '=', product_ids.id),('location_id.usage', 'in', ('internal', 'transit'))])

                    stock_move_id = self.env['stock.move'].search(
                        [('date', '<=', self.date_to), ('date', '>=', self.date_from), ('state', '=', 'done'),
                        ('product_id', '=', product_ids.id)], order="date")

            else:
                stock_movebefore_id = False
                
                if self.warehouse_ids:
                    stock_move_id = self.env['stock.move'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('warehouse_id', 'in', self.warehouse_ids.ids), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
                
                else:
                    stock_move_id = self.env['stock.move'].search(
                        [('state', '=', 'done'), ('product_id', '=', product_ids.id), ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit'))], order="date")
            
            if stock_move_id:

                if stock_quant:
                    for before_stock_quant_ids in stock_quant:
                        amount_before += before_stock_quant_ids.quantity
                res_product = product_ids._compute_quantities_dict(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from)
                qty_available = res_product[product_ids.id]['qty_available']
                if self.warehouse_ids:
                    qty_available = 0
                    for warehouse in self.warehouse_ids:
                        res_product_warehouse = product_ids._compute_quantities_dict_warehouse(lot_id=None, owner_id=None, package_id=None,to_date=self.date_from,warehouse_id=warehouse)
                        qty_available += res_product_warehouse[product_ids.id]['qty_available']

                before_total = qty_available
                amount_qty = qty_available
                
                for stock_move_ids in stock_move_id:
                    if stock_move_ids.location_id.usage not in ('internal', 'transit') and stock_move_ids.location_dest_id.usage in ('internal', 'transit'):

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + stock_move_ids.product_uom_qty
                            qty_9 = stock_move_ids.product_uom_qty

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - stock_move_ids.product_uom_qty
                            qty_11 = stock_move_ids.product_uom_qty

                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            qty_11 = False
                        elif stock_move_ids.location_id.usage == 'internal':
                            qty_9 = False

                        data_list = {
                            "warehouse_id":stock_move_ids.warehouse_id.id,
                            "pd_type_name":pd_type_name,
                            "categ_id":product_ids.categ_id.id,
                            "origin":stock_move_ids.origin,
                            "reference":stock_move_ids.reference,
                            "date":stock_move_ids.date,
                            "default_code":product_ids.default_code,
                            "product_id":product_ids.id,
                            "cost_unit_price":product_ids.standard_price,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "amount_qty":amount_qty,
                            "product_uom_id":product_ids.uom_id.id,
                            "qty_available":qty_available,
                        }
                        stock_movement_results.append(data_list)                        

                    elif stock_move_ids.location_id.usage in ('internal', 'transit') and stock_move_ids.location_dest_id.usage not in ('internal', 'transit'):
                        if stock_move_ids.location_dest_id.usage == 'internal':
                            amount_qty = amount_qty + stock_move_ids.product_uom_qty
                            qty_9 = stock_move_ids.product_uom_qty

                        elif stock_move_ids.location_id.usage == 'internal':
                            amount_qty = amount_qty - stock_move_ids.product_uom_qty
                            qty_11 = stock_move_ids.product_uom_qty

                        if product_ids.type:
                            pd_type = product_ids.type
                            pd_type_name = self.get_selection(pd_type)

                        if stock_move_ids.location_dest_id.usage == 'internal':
                            qty_11 = False
                        elif stock_move_ids.location_id.usage == 'internal':
                            qty_9 = False

                        data_list = {
                            "warehouse_id":stock_move_ids.warehouse_id.id,
                            "pd_type_name":pd_type_name,
                            "categ_id":product_ids.categ_id.id,
                            "origin":stock_move_ids.origin,
                            "reference":stock_move_ids.reference,
                            "date":stock_move_ids.date,
                            "default_code":product_ids.default_code,
                            "product_id":product_ids.id,
                            "cost_unit_price":product_ids.standard_price,
                            "qty_in":qty_9,
                            "qty_out":qty_11,
                            "amount_qty":amount_qty,
                            "product_uom_id":product_ids.uom_id.id,
                            "qty_available":qty_available,
                        }
                        stock_movement_results.append(data_list)
            before_total_sum += before_total            
                        
        ReportLine = self.env["stock.movement.view"]
        self.results = [ReportLine.new(line).id for line in stock_movement_results]
        self.before_total_sum = before_total_sum

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env['ir.actions.report'].search(
            [('report_name', '=', 'stock_movement_report_xlsx'),
             ('report_type', '=', 'xlsx')], limit=1))
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "hdc_stock_card_report.report_stock_movement_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

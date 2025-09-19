from odoo import models, fields, tools, api, _

class TransferLine(models.Model):
    _name = "hdc.transfer.line"
    _description = "Transfer Lines"
    _auto = False

    name = fields.Char("Reference")
    origin = fields.Char("Source Document")
    product_id = fields.Many2one("product.product", "Product")
    picking_id = fields.Many2one("stock.picking", "Picking")
    picking_type_id = fields.Many2one("stock.picking.type", "Picking Type")
    backorder_id = fields.Many2one("stock.move", "Back Order of")
    move_id = fields.Many2one("stock.move", "Stock Move")
    line_id = fields.Many2one("stock.move.line", "Stock Move Line")
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
    )
    date = fields.Datetime("Date")
    location_id = fields.Many2one("stock.location", "Source Location")
    location_dest_id = fields.Many2one("stock.location", "Destination Location")
    qty = fields.Float("Qty")
    remark = fields.Text("Remark")
    uom_id = fields.Many2one("uom.uom", "UoM")
    company_id = fields.Many2one("res.company", "Company")
    print_llk_status = fields.Selection([
        ('no', 'Not Print'),
        ('print', 'Print'),
    ], string="Print LLK Status",default='no')
    urgent_delivery_id = fields.Many2one(
        'urgent.delivery', string='Urgent Delivery Transfer',
    )
    warehouse_status = fields.Selection([
        ('warehouse', 'Inprogress'),
        ('confirmed', 'Confirmed'),
        ('done','Done'),
        ('cancel','Cancelled'),
    ], string='Warehouse Status')
    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Inventory Status',copy=False)
    demand_total = fields.Float(related="move_id.demand_total")
    qty_counted = fields.Float(related="move_id.qty_counted")
    qty_done = fields.Float(related="line_id.qty_done")
    report_qty = fields.Float(compute="compute_report_qty")
    partner_id = fields.Many2one("res.partner", "Customer")
    salesperson_id = fields.Many2one("hr.employee", "Salesperson")
    scheduled_date = fields.Datetime("Scheduled Date")
    sales_type_id = fields.Many2one("sale.order.type", "Sales Type")
    type_borrow = fields.Selection(
        selection=[("not_return", "เบิกไปใช้"), ("must_return", "เบิกยืมคืน")],
        string="Type Borrow",
        default="must_return",
        required=True,
    )


    @api.depends(
        "qty_done",
        "qty_counted",
        "demand_total",
    )
    def compute_report_qty(self):
        for obj in self:
            obj.report_qty = obj.qty_done or obj.qty_counted or obj.demand_total or 0

    def get_report_data(self):
        groups = {}
        for obj in self:
            groups.setdefault(obj.picking_id, self.env[self._name])
            groups[obj.picking_id] |= obj

        docs = []
        for picking_id, lines in groups.items():
            line_vals = {
                'picking_id': picking_id,
                'lines': lines,
            }
            docs.append(line_vals)
        return docs
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f'''
            CREATE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY m.picking_id) AS id,
                    pk.partner_id,
                    pk.sales_type_id,
                    pk.type_borrow,
                    pk.user_employee_id as salesperson_id,
                    pk.scheduled_date,
                    pk.name,
                    pk.origin,
                    pk.backorder_id,
                    pk.company_id,
                    pk.print_llk_status,
                    pk.inventory_status,
                    pk.urgent_delivery_id,
                    pk.warehouse_status,
                    m.picking_id,
                    pt.id as picking_type_id,
                    m.id AS move_id,
                    l.id as line_id,
                    l.date,
                    l.location_id,
                    l.location_dest_id,
                    l.product_id,
                    l.product_qty as qty,
                    l.product_uom_id as uom_id,
                    m.remark,
                    l.state
                FROM 
                    stock_move AS m
                    LEFT JOIN stock_picking AS pk ON pk.id = m.picking_id
                    LEFT JOIN stock_move_line AS l ON l.move_id = m.id
                    LEFT JOIN stock_picking_type AS pt ON pt.id = pk.picking_type_id

                WHERE
                    pt.is_internal_transfer = True
                order by
                    m.date, m.id
                    
            )
        ''')


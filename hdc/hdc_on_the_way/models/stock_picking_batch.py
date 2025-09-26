from odoo import api, fields,_, models
from odoo.fields import first
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockMoveingBatch(models.Model):
    _name = "stock.move.batch.line"
    _description = "Batch Transfer Line"

    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Transfer',
        check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this transfer', copy=False)
    move_id = fields.Many2one(
        'stock.move', 'Stock Move',
        check_company=True,
        states={'done': [('readonly', True)]})
    

class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"
    _description = "Batch Transfer"

    price_total = fields.Monetary(string='Subtotal Amount', compute="_compute_price_total")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id)

    etd = fields.Date(string='ETD',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    eta = fields.Date(string='ETA',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    wh_date = fields.Date(string='WH Date',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    invoice_no = fields.Char(string='Invoice No',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    origin_country = fields.Many2one(
        'res.country', string='Origin Country',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        )
    shipping_provider = fields.Many2one(
        'res.partner', string='Shipping Provider',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        )

    delivery_mode = fields.Many2one(
        'delivery.carrier', string='Delivery Mode',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', domain=[('supplier', '=', True)], states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        )

    warehouse_id = fields.Many2one("stock.warehouse", string = "Warehouse")

    remark = fields.Text(string='Remark', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    
    ###############################################
    
    ## Comment because it's conflix the domain in `_compute_allowed_move_line_tranfer_ids`

    # @api.onchange('picking_type_id')
    # def _onchange_picking_type_id(self):
    #     domain = [("state", "=", "assigned")]
    #     if self.picking_type_id:
    #         domain.append(("picking_type_id", "=", self.picking_type_id.id))
    #     return {'domain': {'move_tranfer_ids': domain}}

    ###############################################

    @api.depends("move_tranfer_ids")
    def _compute_price_total(self):
        for rec in self:
            rec.price_total = sum(ml.price_subtotal for ml in rec.move_tranfer_ids)
 
    move_tranfer_ids = fields.One2many(
        'stock.move','batch_id', string='Stock move lines',domain="[('id', 'in', allowed_move_line_tranfer_ids)]",
        states={'draft': [('readonly', False)], 'in_progress': [('readonly', False)]})
    allowed_move_line_tranfer_ids = fields.One2many('stock.move', compute='_compute_allowed_move_line_tranfer_ids')

    move_line_tranfer_ids = fields.One2many(
        'stock.move.line', string='Stock move lines',
        compute='_compute_batch_move_ids',  readonly=True,
        states={'draft': [('readonly', False)], 'in_progress': [('readonly', False)]})
    
    origin = fields.Char(string='BATCH Ref.')

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        for line in self.move_line_tranfer_ids:
            line.domain_warehouse_id = self.warehouse_id
            if self.warehouse_id:
                putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', line.product_id.id),('location_in_id.warehouse_id', '=', self.warehouse_id.id)],limit = 1)
                if putaway_id:
                    line.location_dest_id = putaway_id.location_out_id.id
                else:
                    line.location_dest_id = self.warehouse_id.lot_stock_id.id
            else:
                line.location_dest_id = self.picking_type_id.default_location_dest_id.id

    def action_fill_on_the_way(self):
        for move in self.move_tranfer_ids:
            # self.move_tranfer_ids.update({'on_the_way': move.product_uom_qty})
            if move.on_the_way <= 0:
                move.on_the_way = move.product_uom_qty

    
    @api.depends('move_tranfer_ids', 'move_line_tranfer_ids')
    def _compute_batch_move_ids(self):
        for batch in self:
            batch.move_ids = batch.move_tranfer_ids
            batch.move_line_tranfer_ids = batch.move_tranfer_ids.move_line_ids
            batch.show_check_availability = any(m.state not in ['assigned', 'done'] for m in batch.move_ids)
            if batch.state not in ['in_progress','done']:
                batch.picking_ids = batch.move_tranfer_ids.mapped('picking_id')

    @api.depends('move_tranfer_ids')
    def _compute_move_ids(self):
        for batch in self:
            batch.move_ids = batch.move_tranfer_ids
            batch.move_line_ids = batch.move_tranfer_ids.move_line_ids
            batch.show_check_availability = any(m.state not in ['assigned', 'done'] for m in batch.move_ids)

    def check_on_the_way(self):
        for batch in self:
            for move in batch.move_tranfer_ids:
                if move.on_the_way == 0 or move.on_the_way > move.product_uom_qty:
                    return True
        return False
    
    def get_move_lines_with_on_the_way_less_than_qty(self):
        move_lines = self.env['stock.move']
        for batch in self:
            move_lines_to_return = batch.move_tranfer_ids.filtered(lambda move: move.on_the_way < move.product_uom_qty)
            move_lines |= move_lines_to_return
        return move_lines
    
    def find_missing_move_lines(self):
        missing_move_lines = self.env['stock.move']
        move_ids = self.move_tranfer_ids.picking_id.move_ids_without_package
        for batch in self:
            move_lines_in_move_line_transfer = set(batch.move_tranfer_ids.ids)
            move_lines_in_picking = set(move_ids.ids)
            move_lines_to_search = list(move_lines_in_picking - move_lines_in_move_line_transfer)
            missing_move_lines |= self.env['stock.move'].search([
                ('id', 'in', move_lines_to_search),
            ])
        return missing_move_lines
    
    def action_revise(self):
        self.state = 'draft'
        self.show_check_availability = False
        if self.state == "draft":
            self.warehouse_status = "warehouse"
            self.inventory_status = 'waiting'
            self.confirm_picking_date = False
            self.user_confirm_picking = False
            self.validation_picking_date = False
            self.user_validation_picking = False
            for move in self.move_ids:
                move.picking_id.warehouse_status = "warehouse"
                move.picking_id.inventory_status = "waiting"
                move.picking_id.confirmed_warehouse_date = False
                move.picking_id.user_confirm_warehouse_id = False
                move.picking_id.validate_date = False
                move.picking_id.validate_user_id = False

    def action_confirm(self):
        if not self.move_tranfer_ids :
            raise UserError(_("You have to set some pickings to batch."))
        check_on_the_way  = self.check_on_the_way()
        # if check_on_the_way :
        #     raise UserError(_("Please Check On The Way Value."))
        find_missing_move_lines = self.find_missing_move_lines()
        if find_missing_move_lines :
            raise UserError(_("Please Select all product in %s.",find_missing_move_lines[:1].origin))
        self.move_line_tranfer_ids.unlink()
        self.move_tranfer_ids._action_assign()
        for move in self.move_tranfer_ids:
            for move_line in move.move_line_ids:
                move_line.write({'qty_done':move.on_the_way})
        self.state = 'in_progress'
    
    def create_stock_move(self, picking_id,product_uom_qty,line):
        stock_move = self.env['stock.move'].create({
            'picking_id': picking_id,
            'origin': line.origin,
            'batch_id': False,
            'name': line.product_id.display_name,
            'product_id': line.product_id.id,
            'product_uom_qty': product_uom_qty,
            'reserved_availability': product_uom_qty,
            'product_uom': line.product_uom.id,  
            'location_id': line.location_id.id,
            'location_dest_id': line.location_dest_id.id,
            'picking_type_id': line.picking_type_id.id,
            
        })
        if line.purchase_line_id.id :
            stock_move.write({
                'purchase_line_id': line.purchase_line_id.id,
            })
        return stock_move.id

    def create_backorder(self,create_back_order = False):
        """Sanity checks, confirm the pickings and mark the batch as confirmed."""
        self.ensure_one()
        
        find_missing_move_lines = self.find_missing_move_lines()
        get_move_lines_with_on_the_way_less_than_qty  = self.get_move_lines_with_on_the_way_less_than_qty()
        missing_move_ids = find_missing_move_lines.ids
        combined_move_ids = get_move_lines_with_on_the_way_less_than_qty.ids + find_missing_move_lines.ids
        moves_by_picking = {}
    
        for move_id in combined_move_ids:
            move = self.env['stock.move'].browse(move_id)
            picking_id = move.picking_id.id
            if picking_id not in moves_by_picking:
                moves_by_picking[picking_id] = self.env['stock.move']
            moves_by_picking[picking_id] |= move
        if create_back_order == 1 :
            
            for picking_id, move_lines in moves_by_picking.items():
                
                has_missing_moves = any(move.id in missing_move_ids for move in move_lines)
                filtered_move_lines = move_lines.filtered(lambda move: move.id in missing_move_ids)
                move_lines_etc = move_lines.filtered(lambda move: move.id not in missing_move_ids)
                picking_data = {
                    'company_id': move_lines.picking_id.company_id.id,
                    'batch_id': False,
                    'origin': move_lines.picking_id.origin,
                    'scheduled_date': move_lines.picking_id.scheduled_date,
                    'date_deadline': move_lines.picking_id.date_deadline,
                    'picking_type_id': move_lines.picking_id.picking_type_id.id,
                    'partner_id': move_lines.picking_id.partner_id.id,
                    'location_id': move_lines.picking_id.location_id.id,
                    'location_dest_id': move_lines.picking_id.location_dest_id.id,
                }
                backorder = self.env['stock.picking'].create(picking_data)
                if move_lines.picking_id.purchase_id.id :
                    backorder.write({
                        'purchase_id': move_lines.picking_id.purchase_id.id, 
                    })
                
                move_ids_without_package = []
                for line in move_lines_etc:
                    product_uom_qty = line.product_uom_qty - line.on_the_way 
                    move_new = self.create_stock_move(backorder.id,product_uom_qty,line)
                    line.product_uom_qty =  line.on_the_way 
                    line.reserved_availability =  line.on_the_way 
                if has_missing_moves:
                    for move in filtered_move_lines:
                        move_new = self.create_stock_move(backorder.id,move.product_uom_qty,move)
                        move.write({'state':'draft'})
                        move.unlink()
            backorder.action_assign()
            backorder.action_confirm()
        else:
            for picking_id, move_lines in moves_by_picking.items():
                filtered_move_lines = move_lines.filtered(lambda move: move.id in missing_move_ids)
                move_lines_etc = move_lines.filtered(lambda move: move.id not in missing_move_ids)
                if move_lines_etc:
                    for line in move_lines_etc:
                        line.product_uom_qty =  line.on_the_way 
                        line.reserved_availability =  line.on_the_way
                if filtered_move_lines:
                    picking_data = {
                        'company_id': move_lines.picking_id.company_id.id,
                        'batch_id': False,
                        'origin': move_lines.picking_id.origin,
                        'scheduled_date': move_lines.picking_id.scheduled_date,
                        'date_deadline': move_lines.picking_id.date_deadline,
                        'picking_type_id': move_lines.picking_id.picking_type_id.id,
                        'partner_id': move_lines.picking_id.partner_id.id,
                        'location_id': move_lines.picking_id.location_id.id,
                        'location_dest_id': move_lines.picking_id.location_dest_id.id,
                    }
                    backorder = self.env['stock.picking'].create(picking_data)
                    if move_lines.picking_id.purchase_id.id :
                        backorder.write({
                            'purchase_id': move_lines.picking_id.purchase_id.id, 
                        })
                    
                    
                    for move in filtered_move_lines:
                        move_new = self.create_stock_move(backorder.id,move.product_uom_qty,move)
                        move.write({'state':'draft'})
                        move.unlink()
                    backorder.action_assign()
                    backorder.action_confirm()

        self._check_company()
        self.state = 'in_progress'
        return True
    
    @api.onchange('partner_id','state','picking_type_id')
    def _onchange_reset_domain(self):
        self._compute_allowed_move_line_tranfer_ids()
    
    def _compute_allowed_move_line_tranfer_ids(self):
        allowed_picking_states = ['waiting', 'confirmed', 'assigned']
        cancelled_batchs = self.env['stock.picking.batch'].search_read([('state', '=', 'cancel')], ['id'])
        cancelled_batch_ids = [batch['id'] for batch in cancelled_batchs]

        for batch in self:
            domain = []            
            domain_states = list(allowed_picking_states)
            # Allows to add draft pickings only if batch is in draft as well.
            if batch.state == 'draft':
                domain_states.append('draft')
            if batch.partner_id:
                domain += [('partner_id', '=', batch.partner_id.id)]
            if batch.picking_type_id:
                domain += [('picking_type_id', '=', batch.picking_type_id.id)]
            domain += [
                ('company_id', '=', batch.company_id.id),
                ('state', 'in', domain_states),
                '|',
                '|',
                ('batch_id', '=', False),
                ('batch_id', '=', batch.id),
                ('batch_id', 'in', cancelled_batch_ids),
            ]     
            batch.allowed_move_line_tranfer_ids = self.env['stock.move'].search(domain)
    
class StockMove(models.Model):
    _inherit = "stock.move"

    lot_serial_num = fields.Many2one('stock.production.lot', string="Lot/Serial Number")

    price_subtotal = fields.Monetary(string='Subtotal', compute="_compute_price_subtotal")

    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.company.currency_id)
    
    on_the_way = fields.Float(string='Shipped', copy=False)
    default_code = fields.Char(string='Internal Reference',related='product_id.default_code')
    # brand = fields.Many2one(comodel_name="product.brand",related='product_id.product_brand_id', string = 'Brand',index=True)
    brand = fields.Many2one(comodel_name="product.brand",related='product_id.product_brand_id', string = 'Brand')
    qty_available = fields.Float(related='product_id.qty_available', string = 'Quantity On Hand')
    virtual_available = fields.Float(related='product_id.virtual_available', string = 'Forecasted Quantity')
    picking_state = fields.Selection(string='Status',related='picking_id.state')
    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Transfer',
        check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this transfer', copy=False)
    batch_state = fields.Selection(string='Batch Status',related='batch_id.state')

    @api.depends("price_unit", "on_the_way")
    def _compute_price_subtotal(self):
        for rec in self:
            if rec.price_unit and rec.on_the_way:
                rec.price_subtotal = rec.on_the_way * rec.price_unit
            else:
                rec.price_subtotal = 0
    
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    domain_warehouse_id = fields.Many2one("stock.warehouse", string = "Warehouse")
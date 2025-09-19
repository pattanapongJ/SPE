from email.policy import default
import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date


class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    remark = fields.Char(string="Remark")
    return_value = fields.Float(string="Return", readonly=True)
    scrap_value = fields.Float(string="Scrap", readonly=True)
    scrap_return = fields.Float(string="Scrap", readonly=True)
    # product_brand = fields.Many2one(string="Brand", related="product_id.product_brand_id")
    # product_model = fields.Many2one(string="Model", related="product_id.product_model_id")

class StockPicking(models.Model):

    _inherit = 'stock.picking'
    
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'กรุณาตรวจสอบ Sequence เนื่องจากอาจจะระบุผิดพลาด กรุณาติดต่อผู้ดูแลระบบ!'),
    ]
    
    
    requestor_emp = fields.Many2one("res.users", string="Requestor", default=lambda self: self.env.user)
    department_name = fields.Many2one("hr.department", string="Department", related="requestor_emp.department_id")
    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now)
    return_date = fields.Datetime(string="Return Date")
    operation_types = fields.Char(related='picking_type_id.addition_operation_types.addition_Operation_type')
    addition_operation_types = fields.Many2one(related = 'picking_type_id.addition_operation_types')
    addition_operation_types_code = fields.Char(related='addition_operation_types.code')
    state = fields.Selection(selection_add=[("ready_delivery", "Ready Delivery"),("done",)],)
    borrow_date = fields.Datetime(string='Borrowed Date', default=fields.Datetime.now)
    approver_return = fields.Many2one('res.partner', string="Approver")
    reviewer_return = fields.Many2one('res.partner', string="Reviewer")
    request_spare_parts_type = fields.Boolean(string="Request spare parts Type",default=False)
    transfer_date = fields.Datetime(string="Transfer Date", readonly=True)
    # transfer_date = fields.Datetime(
    #     'Transfer Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
    #     index=True, default=fields.Datetime.now, tracking=True,
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    #     help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    operation_type_rm = fields.Char(related='picking_type_id.sequence_code')
    check_force_done = fields.Boolean(string="Force Done", compute='_compute_check_force_done') 
    check_order_return = fields.Boolean(string="Order Return Check", compute='_compute_check_order_return')     

    # def _compute_scheduled_date(self):
    #     result = super(StockPicking, self)._compute_scheduled_date()  

    #     return result

    @api.onchange('picking_type_id')
    def _default_external_tranfer_type(self):
        res = super(StockPicking, self)._default_external_tranfer_type()
        self.request_spare_parts_type == False
        self.check_all == False
        if self.picking_type_id:
            addition_operation_type = self.env['stock.picking.type'].browse(
                self.picking_type_id.id).addition_operation_types
            if addition_operation_type:
                if addition_operation_type.code == "AO-02":
                    self.request_spare_parts_type = True
                else:
                    self.request_spare_parts_type = False
            else:
                self.request_spare_parts_type = False
                self.check_all = False
        else:
            self.request_spare_parts_type = False
            self.check_all = False
        if self.request_spare_parts_type:
            self.check_all = True


    def get_return_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order Return',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', "Return of "+self.name)],
            'context': {'create': False,},
        }

    @api.depends('move_ids_without_package', 'move_ids_without_package.return_done', 'move_ids_without_package.quantity_done')
    def _compute_check_order_return(self):
        for record in self:
            # move_lines = record.move_ids_without_package
            check_order_return = False

            for record in self:
                return_ids = record.env['stock.picking'].search([('return_picking_form_id', '=', record.id)])
                return_arr = []
                # record.check_force_done = False
                if return_ids:
                    change_return = record.env['stock.move'].search([('picking_id', '=', record.id)])
                    for line in change_return:
                        if line.return_done != line.quantity_done:
                            return_arr.append(line.id)

                    if not return_arr:
                        if record.state == "ready_delivery":
                            record.write({'state': 'done'})
                

            record.check_order_return = check_order_return



    @api.depends('move_ids_without_package', 'move_ids_without_package.return_done', 'move_ids_without_package.quantity_done')
    def _compute_check_force_done(self):
        for record in self:
            move_lines = record.move_ids_without_package
            check_force_done = False

            for line in move_lines:
                if line.return_done != line.quantity_done:
                    check_force_done = True
                    break
                

            record.check_force_done = check_force_done

    def force_done(self):
        if self.check_force_done:
            if self.state == 'ready_delivery':
                change_return = self.env['stock.move'].search([('picking_id', '=', self.id)])
                change_state = self.env['stock.picking'].search([('id', '=', self.id)])

                return_ids = self.env['stock.picking'].search([('return_picking_form_id', '=', self.id)])
                
                return_arr = []
                for line in return_ids:
                    if line.state == 'assigned' or line.state == 'waiting':
                        return_arr.append(line.id)
                        language = self.env.context.get('lang')
                        if language == 'th_TH':
                            raise ValidationError(_("กรุณายกเลิกใบรับสินค้าก่อนทำการยกเลิกใบเบิกยืมสินค้า."))
                        else:
                            raise ValidationError(_("Please cancel the Receipt document before canceling the Borrow document."))

                if not return_arr:
                    if self.state == "ready_delivery":
                        self.write({'state': 'done'})

                    # else:
                    #     self.state = "done"
                # for line in change_return:
                #     if line.return_value + line.scrap_value == change_return[0].quantity_done:
                #         language = self.env.context.get('lang')
                #         if language == 'th_TH':
                #             raise ValidationError(_("กรุณายกเลิกใบรับสินค้าก่อนทำการยกเลิกใบเบิกยืมสินค้า."))
                #         else:
                #             raise ValidationError(_("Please cancel the Receipt document before canceling the Borrow document."))
                #     else:
                #         self.state = "done"
    def _action_done(self):
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'ready_delivery', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': fields.Datetime.now(), 'priority': '0'})

        # if incoming moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True
    def _button_validation_borrow(self):
        if self.operation_types == "Request spare parts Type":
            # Clean-up the context key at validation to avoid forcing the creation of immediate
            # transfers.
            ctx = dict(self.env.context)
            ctx.pop('default_immediate_transfer', None)
            self = self.with_context(ctx)

            # Sanity checks.
            pickings_without_moves = self.browse()
            pickings_without_quantities = self.browse()
            pickings_without_lots = self.browse()
            products_without_lots = self.env['product.product']
            for picking in self:
                if not picking.move_lines and not picking.move_line_ids:
                    pickings_without_moves |= picking

                picking.message_subscribe([self.env.user.partner_id.id])
                picking_type = picking.picking_type_id
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
                no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
                if no_reserved_quantities and no_quantities_done:
                    pickings_without_quantities |= picking

                if picking_type.use_create_lots or picking_type.use_existing_lots:
                    lines_to_check = picking.move_line_ids
                    if not no_quantities_done:
                        lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                    for line in lines_to_check:
                        product = line.product_id
                        if product and product.tracking != 'none':
                            if not line.lot_name and not line.lot_id:
                                pickings_without_lots |= picking
                                products_without_lots |= product

            if not self._should_show_transfers():
                if pickings_without_moves:
                    raise UserError(_('Please add some items to move.'))
                if pickings_without_quantities:
                    raise UserError(self._get_without_quantities_error_message())
                if pickings_without_lots:
                    raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
            else:
                message = ""
                if pickings_without_moves:
                    message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
                if pickings_without_quantities:
                    message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
                if pickings_without_lots:
                    message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
                if message:
                    raise UserError(message.lstrip())

            # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
            # moves and/or the context and never call `_action_done`.
            if not self.env.context.get('button_validate_picking_ids'):
                self = self.with_context(button_validate_picking_ids=self.ids)
            res = self._pre_action_done_hook()
            if res is not True:
                return res

            # Call `_action_done`.
            if self.env.context.get('picking_ids_not_to_backorder'):
                pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
                pickings_to_backorder = self - pickings_not_to_backorder
            else:
                pickings_not_to_backorder = self.env['stock.picking']
                pickings_to_backorder = self
            pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
            pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

            self.write({'state': 'ready_delivery'})
            self.write({'transfer_date': fields.Datetime.now()})
            self.set_sale_borrow_qty()

            return True

    def button_validate(self):
        if len(self) > 1:
            for picking in self:
                picking._button_validation_borrow()
        else:
            res = self._button_validation_borrow()
            if res:
                return res

        return super(StockPicking, self).button_validate()
    
    order_return = fields.Integer(compute='compute_order_rfq_count')
    def compute_order_rfq_count(self):
        for record in self:
            record.order_return = self.env['stock.picking'].search_count(
                [('return_picking_form_id', '=', self.id)])
            
    def set_sale_borrow_qty(self):
        pass


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    _description = 'Return Picking'

    remark = fields.Text(string="Remark", required=True)
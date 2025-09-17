# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class PickingList(models.Model):

    _inherit = 'picking.lists'

    confirm_picking_date = fields.Datetime(string="Confirmed Warehouse Date", readonly=True)
    user_confirm_picking = fields.Char(string="Confirmed Warehouse", readonly=True)
    validation_picking_date = fields.Datetime(string="Validate Inventory Date", readonly=True, tracking=True)
    user_validation_picking = fields.Char(string="Validate Inventory", readonly=True, tracking=True)
    warehouse_status = fields.Selection([('warehouse', 'Inprogress'),('done','Done'),('cancel','Cancelled')],
                                        default='warehouse', string='Warehouse Status',copy=False,compute='_compute_access_right_value',)
    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Inventory Status',copy=False,compute='_compute_access_right_value',)

    access_right_value = fields.Selection(
        selection=[
            ('all', 'Admin Picking List'),
            ('confirm', 'Confirm Picking Qty'),
            ('validate', 'Validate Picking Done')
        ],
        string="Access Right Value",
        compute='_compute_access_right_value',
    )

    # @api.onchange('list_line_ids.amount_arranged')
    # def _onchange_list_line_ids_amount_arranged(self):
    #     print('--------self.user_id.access_right------------', self.user_id.access_right)

    # @api.depends('user_id.access_right')
    def _compute_access_right_value(self):
        # for record in self:
        #     if record.user_id.access_right:
        #         record.access_right_value = record.user_id.access_right
        #     else:
        #         record.access_right_value = False

        for record in self:
            if self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and not self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'confirm'
            elif not self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'validate'
            elif self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'all'
            else:
                record.access_right_value = False

            if record.state == 'draft':
                record.warehouse_status = 'warehouse'
                record.inventory_status = 'waiting'
            elif record.state == 'waiting_pick':
                record.warehouse_status = 'done'
                record.inventory_status = 'progress'
            elif record.state == 'done':
                record.warehouse_status = 'done'
                record.inventory_status = 'done'
            else:
                record.warehouse_status = "cancel"
                record.inventory_status = "cancel"

    def action_confirm(self):
        if self.list_line_ids:
            for line in self.list_line_ids.filtered(lambda x:x.state != 'cancel'):
                if line.amount_arranged <= 0:
                    raise UserError('Please Check Picking QTY')
        result = super(PickingList, self).action_confirm()
        self.confirm_picking_date = fields.Datetime.now()
        self.user_confirm_picking = self.env.user.name or ''
        
            
        return result

    def action_validate(self):
        result = super(PickingList, self).action_validate()
        self.validation_picking_date = fields.Datetime.now()
        self.user_validation_picking = self.env.user.name or ''
        
        return result
    
    def action_cancel(self):
        result = super(PickingList, self).action_cancel()
        for rec in self:
            rec.state = "cancel"

        return result
    
class PickingListLine(models.Model):
    _inherit = 'picking.lists.line'

    access_right_value = fields.Selection(
        selection=[
            ('all', 'All'),
            ('confirm', 'Confirm'),
            ('validate', 'Validate')
        ],
        string="Access Right Value",
        compute='_compute_access_right_value',
    )

    # @api.depends('picking_lists.access_right_value')
    # def _compute_access_right_value(self):
    #     for record in self:
    #         if record.picking_lists.access_right_value:
    #             record.access_right_value = record.picking_lists.access_right_value
    #         else:
    #             record.access_right_value = False

    def _compute_access_right_value(self):


    # "hdc_picking_list_access_right.group_all"
    # "hdc_picking_list_access_right.group_confirm"
    # "hdc_picking_list_access_right.group_validate"

        for record in self:
            if self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and not self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'confirm'
            elif not self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'validate'
            elif self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
                record.access_right_value = 'all'
            else:
                record.access_right_value = False

    # @api.onchange('amount_arranged')
    # def _onchange_amount_arranged(self):

    #     for record in self:
    #         if self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and not self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
    #             print('------------confirm------------')
    #         elif not self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
    #             print('------------validate------------')
    #         elif self.env.user.has_group('hdc_picking_list_access_right.group_confirm') and self.env.user.has_group('hdc_picking_list_access_right.group_validate'):
    #             print('------------all------------')
    #         else:
    #             print('------------False------------')

        


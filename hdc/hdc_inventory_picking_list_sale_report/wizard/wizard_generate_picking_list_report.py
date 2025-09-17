# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError

class WizardGeneratePickingListReport(models.TransientModel):
    _name = 'wizard.generate.picking.list.report'
    _description = "Wizard Generate Picking List Report"

    def _get_user_warehouse_domain(self):
        company_ids = self.env.user.company_ids.ids or [self.env.company.id]
        return [('company_id', 'in', company_ids)]
    
    def _get_warehouse_domain(self):
        return [('user_ids', 'in', self.env.user.id)]
    
    picking_list_ids = fields.Many2many(
        comodel_name='picking.lists',
        string='Picking Lists',
    )
    project_name = fields.Many2one('sale.project', string='Project Name')
    partner_id = fields.Many2many(
        "res.partner",
        string="Customer",
        domain="[('customer', '=', True)]"
    )
    origin = fields.Char(string='PL Ref.')
    sale_id = fields.Many2many("sale.order", string = "SO No.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_pick', 'Waiting for pickup'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', default='draft')
    warehouse_id = fields.Many2one(comodel_name = "stock.warehouse", string = "Warehouse", domain=_get_warehouse_domain)
    location_id = fields.Many2one('stock.location', string = 'Source Location', domain=_get_user_warehouse_domain)
    sale_type_id = fields.Many2one(comodel_name="sale.order.type", string="Sale Type")
    user_id = fields.Many2one('res.users', string = 'Responsible')
    date = fields.Datetime("Pick Date")
    delivery_date_from = fields.Date("Ship Date From")
    delivery_date_to = fields.Date("Ship Date To")
    checker = fields.Many2one('res.users', string='Checker')
    checker_date = fields.Datetime("Checker Date")
    barcode_date = fields.Date(string="Barcode Date")
    

    @api.constrains('delivery_date_from', 'delivery_date_to')
    def _check_delivery_date_range(self):
        for rec in self:
            if rec.delivery_date_from and not rec.delivery_date_to:
                raise ValidationError(_("Please fill in 'Ship Date To' when 'Ship Date From' is set."))
            if rec.delivery_date_to and not rec.delivery_date_from:
                raise ValidationError(_("Please fill in 'Ship Date From' when 'Ship Date To' is set."))
            if rec.delivery_date_from and rec.delivery_date_to:
                if rec.delivery_date_from > rec.delivery_date_to:
                    raise ValidationError(_("Ship Date From must be earlier than or equal to Ship Date To."))

    def action_generate_report(self):
        self.ensure_one()

        domain = []

        if self.picking_list_ids:
            domain.append(('id', 'in', self.picking_list_ids.ids))
        if self.project_name:
            domain.append(('project_name', '=', self.project_name.id))
        if self.partner_id:
            domain.append(('partner_id', 'in', self.partner_id.ids))
        if self.origin:
            domain.append(('origin', 'ilike', self.origin))
        if self.sale_id:
            domain.append(('sale_id', 'in', self.sale_id.ids))
        if self.state:
            domain.append(('state', '=', self.state))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))
        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))
        if self.date:
            domain.append(('date', '>=', self.date))
        # if self.delivery_date:
        #     domain.append(('delivery_date', '>=', self.delivery_date))
        if self.checker:
            domain.append(('checker', '=', self.checker.id))
        if self.checker_date:
            domain.append(('checker_date', '>=', self.checker_date))
        if self.barcode_date:
            domain.append(('barcode_date', '=', self.barcode_date))
        if self.sale_type_id:
            domain.append(('sale_type_id', '=', self.sale_type_id.id))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.delivery_date_from and self.delivery_date_to:
            domain.append(('delivery_date', '>=', self.delivery_date_from))
            domain.append(('delivery_date', '<=', self.delivery_date_to))

        # if self.delivery_date_from:
        #     domain.append(('delivery_date', '>=', self.delivery_date_from))
        # if self.delivery_date_to:
        #     domain.append(('delivery_date', '<=', self.delivery_date_to))



        picking_lists = self.env['picking.lists'].search(domain, order='create_date desc')

        if not picking_lists:
            raise UserError(_("No matching picking lists found."))

        # สร้าง record ใน generate.picking.list.report
        report = self.env['generate.picking.list.report'].create({
            'picking_list_ids': [(6, 0, picking_lists.ids)],
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'project_name': self.project_name.id,
            'origin': self.origin,
            'sale_id': [(6, 0, self.sale_id.ids)],
            'state': self.state,
            'warehouse_id': self.warehouse_id.id,
            'location_id': self.location_id.id,
            'sale_type_id': self.sale_type_id.id,
            'user_id': self.user_id.id,
            'date': self.date,
            'delivery_date_from': self.delivery_date_from,
            'delivery_date_to': self.delivery_date_to,
            'checker': self.checker.id,
            'checker_date': self.checker_date,
            'barcode_date': self.barcode_date,
            'generate_line_ids': [
                (0, 0, {'picking_list_id': pl.id})
                for pl in picking_lists
            ],
        })


        return report.env.ref(
            'hdc_inventory_picking_list_sale_report.generate_picking_list_report'
        ).report_action(report)

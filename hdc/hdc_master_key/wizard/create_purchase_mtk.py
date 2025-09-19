# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WizardCreatePurchaseMTK(models.TransientModel):
    _name = "wizard.create.purchase.mtk"
    _description = "Wizard Create"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    operation_type = fields.Many2one('stock.picking.type', 
                                     string='Resupply',
                                     domain="[('is_master_key_resupply_subcontract', '=', True), ('company_id', '=', company_id)]",
                                     required=True)
    
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    
    def action_create_purchase_master_key(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        purchase_order_obj = self.env['purchase.order'].with_company(company_id)
        purchase_line_obj = self.env['purchase.order.line']
        StockPicking = self.env['stock.picking']
        
        for sale in self.sale_id:
            if sale.purchase_master_key_id:
                raise UserError(
                            _(
                                "คุณเคยสร้างใบ MTK แล้ว"
                            )
                        )

            dummy_vendor = self.env['res.partner'].search([
                ('is_vendor_dummy', '=', True),
                '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)
            ], limit=1)

            if not dummy_vendor:
                raise UserError(_("กรุณาสร้างระบุ Vendor Dummy"))
            

            order_type = self.env["purchase.order.type"].search([("is_master_key_type", "=", True), ("company_id", "=", self.company_id.id)], limit=1)

            purchase_order = purchase_order_obj.create({
                'partner_id': dummy_vendor.id,   
                'is_master_key': sale.is_master_key,
                'order_type': order_type.id if order_type else False,
                'origin': sale.name,
                'picking_type_id': self.operation_type.id if self.operation_type else False,
                "company_id":self.company_id.id,
                'order_line': [],
            })

            if not sale.purchase_master_key_id:
                sale.purchase_master_key_id = purchase_order.id
                
            for line in sale.order_line:
                if line.product_id.type == 'service' and line.product_id.is_master_key_service:
                    purchase_line_obj.create({
                        'order_id': purchase_order.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom': line.product_uom.id,
                        'product_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                    })

            if not purchase_order.order_type:
                purchase_order.order_type = purchase_order._default_order_type()

            purchase_order.button_confirm_inter_com()
            purchase_order.confirm_po()

        return {
            'name': _('Purchase Order'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'type': 'ir.actions.act_window',
        }

        
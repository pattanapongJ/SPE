# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):
    _inherit = "sale.order"

    inter_company_transactions = fields.Boolean(related = "type_id.inter_company_transactions")
    inter_so_company = fields.Char(string="Ref. SO inter company", copy=False)
    inter_so_company_count = fields.Integer(compute = "_compute_inter_company_count")
    inter_po_company_count = fields.Integer(compute = "_compute_inter_company_count")
    count_so_inter = fields.Integer(compute = "_compute_inter_company_count")

    def _compute_inter_company_count(self):
        for rec in self:
            purchase_id = self.env['purchase.order'].search([('inter_so_company', '=', rec.name)])
            if purchase_id:
                rec.inter_po_company_count = len(purchase_id)
            else:
                rec.inter_po_company_count = 0
            if rec.inter_so_company:
                so_id = self.search([('name', '=', rec.inter_so_company)])
                rec.inter_so_company_count = len(so_id)
            else:
                rec.inter_so_company_count = 0

            so_ids = self.env['sale.order'].search([('inter_so_company', '=', rec.name)])
            rec.count_so_inter = len(so_ids) if so_ids else 0

    def action_so_inter_company(self):
        if self.inter_company_transactions:
            so_ids = self.env['sale.order'].search([('name', '=', self.inter_so_company)])
        else:
            so_ids = self.env['sale.order'].search([('inter_so_company', '=', self.name)])
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            }
        if len(so_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': so_ids.id,
                })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', so_ids.ids)],
                'name': _("Sale Orders"),
                })
        return action

    def action_po_inter_company(self):
        po_ids = self.env['purchase.order'].search([('inter_so_company', '=', self.name)])
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            }
        if len(po_ids) == 1:
            action.update({
                'view_mode': 'form', 'res_id': po_ids.id,
                })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', po_ids.ids)],
                'name': _("Purchase Orders"),
                })
        return action

    # @api.onchange("team_id")
    # def _domain_type_id(self):
    #     if self.team_id:
    #         sale_type_list = self.team_id.sale_type_ids.ids
    #         sale_type_inter_company = self.env["sale.order.type"].search([('inter_company_transactions', '=', True), ("company_id", "=", self.company_id.id)])
    #         if sale_type_inter_company:
    #             sale_type_list += sale_type_inter_company.ids
    #         return {
    #             "domain": {"type_id": [("id", "in", sale_type_list), ("company_id", "=", self.company_id.id)]}
    #         }
    #     else:
    #         return {"domain": {"type_id": []}}

    def action_sale_ok2(self):
        if self.type_id.inter_company_transactions == True:
            purchase_id = self.env["purchase.order"].search(
                [('origin', '=', self.name), ("inter_company_transactions", "=", True), ("state", "!=", "cancel")],
                limit = 1)
            if not purchase_id:
                raise UserError(_("กรุณาตรวจสอบระบบยังไม่ตรวจพบการสร้าง PO"))
            else:
                res = self.action_sale_ok()
                for pick in self.picking_ids.filtered(lambda l: l.state != "cancel"):
                    pick.action_assign()
                    if pick.state != "assigned":
                        UserError(_("กรุณาตรวจสอบจำนวนสินค้า"))
                    for move in pick.move_lines:
                        move.quantity_done = move.product_uom_qty
                    button_validate = pick.with_context(skip_immediate = True).with_context(skip_backorder = True).button_validate()

                if self.state in ('done', 'sale'):
                    ctx = {'active_model': 'sale.order', 'active_ids': self.ids}
                    create_invoice_wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
                        {'advance_payment_method': 'delivered'})
                    create_invoice_wizard.create_invoices()
                return res
        else:
            return self.action_sale_ok()

    def action_inter_company(self):
        # if self.type_id.inter_company_transactions == True:
        line_ids_so = []
        line_ids_po = []

        pricelist_id = self.env["product.pricelist"].search([('inter_company_transactions', '=', True)], limit = 1)
        if not pricelist_id:
            raise UserError(_("ไม่มี Pricelist จัดซื้อระหว่างกัน"))
        if self.order_line:
            for line in self.order_line:
                if line.product_id.type != "service":
                    # pricelist_item = self.env["product.pricelist.item"].search(
                    #     [("product_id", "=", line.product_id.id), ("pricelist_id", "=", pricelist_id.id)],
                    #     limit = 1)
                    # ค้นหา pricelist items ทั้งหมดสำหรับ pricelist นี้ เรียงตาม min_quantity จากมากไปน้อย
                    pricelist_search = self.env["product.pricelist.item"].search([("pricelist_id", "=", pricelist_id.id)], order='min_quantity desc')
                    
                    # กรองตามวันที่ที่มีผล
                    current_date = fields.Datetime.now()
                    pricelist_search = pricelist_search.filtered(lambda x: 
                        # ไม่มีการจำกัดวันที่เริ่มต้น หรือ วันที่เริ่มต้น <= วันที่ปัจจุบัน
                        (not x.date_start or x.date_start <= current_date) and
                        # ไม่มีการจำกัดวันที่สิ้นสุด หรือ วันที่สิ้นสุด >= วันที่ปัจจุบัน  
                        (not x.date_end or x.date_end >= current_date)
                    )
                    
                    # กรองตามจำนวนขั้นต่ำ
                    pricelist_search = pricelist_search.filtered(lambda x: 
                        x.min_quantity <= line.product_uom_qty
                    )
                    
                    # กรองตามสินค้า (ตรงกันทั้ง product_id หรือ product_tmpl_id)
                    pricelist_item = pricelist_search.filtered(lambda x: 
                        x.product_id.id == line.product_id.id or 
                        x.product_tmpl_id.id == line.product_id.product_tmpl_id.id
                    )
                    
                    # เลือกรายการแรก (ที่มี min_quantity สูงสุดที่ตรงเงื่อนไข) หรือให้เป็น empty recordset
                    pricelist_item = pricelist_item[:1] if pricelist_item else False
                    if pricelist_item:
                        price_unit = pricelist_item.fixed_price if not line.free_product else 0.0
                        triple_discount = pricelist_item.triple_discount
                        dis_price = pricelist_item.dis_price
                        cost_price_list = pricelist_item.fixed_price if not line.free_product else 0.0
                        cost_price = pricelist_item.pricelist_cost_price
                    else:
                        price_unit = 0.0
                        triple_discount = ''
                        dis_price = 0.0
                        cost_price_list = 0.0
                        cost_price = 0.0
                    res_product = line.product_id._compute_quantities_dict_company(lot_id = None, owner_id = None,
                                                                               package_id = None,
                                                                               company_id = self.company_id)
                    free_qty = res_product[line.product_id.id]['free_qty']
                    line_ids_so.append((0, 0, {
                        'order_line': line.id, 'product_id': line.product_id.id,
                        'categ_id': line.product_id.categ_id.id, 'product_uom_qty': line.product_uom_qty,
                        'order_qty': line.product_uom_qty, 'product_uom': line.product_uom.id,
                        'price_unit': price_unit,
                        'triple_discount': triple_discount,
                        'free_qty': free_qty,
                        'unit_price_pricelist': dis_price,
                        'free_product': line.free_product,
                        'cost_price_list': cost_price_list,
                        'cost_price': cost_price,
                        }))
                    
                    line_ids_po.append((0, 0, {
                        'order_line': line.id, 'product_id': line.product_id.id,
                        'categ_id': line.product_id.categ_id.id, 'product_uom_qty': line.product_uom_qty,
                        'order_qty': line.product_uom_qty, 'product_uom': line.product_uom.id,
                        'price_unit': price_unit,
                        'triple_discount': triple_discount,
                        'free_qty': free_qty,
                        'free_product': line.free_product,
                        'cost_price_list': cost_price_list
                        }))


        wizard = self.env["wizard.sale.inter.company"].create({
            "sale_id": self.id, "pricelist_id": pricelist_id.id, "order_line": line_ids_so,"order_po_line": line_ids_po
            })
        action = {
            'name': 'Create Inter Company',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.sale.inter.company',
            'res_id': wizard.id, 'view_mode': 'form',
            "target": "new",
            }
        return action
    
    @api.onchange('type_id')
    def _onchange_sale_type_inter_company(self):
        partner_invoice_id = [('customer', '=', True)]
        partner_shipping_id = [('customer', '=', True)]
        res = {}
        domain_partner = [('customer', '=', True)]

        if self.type_id.inter_company_transactions == True:
            partner_invoice_id = [('inter_company_customer', '=', True)]
            partner_shipping_id = [('inter_company_customer', '=', True)]
            res = {}
            domain_partner = [('inter_company_customer', '=', True)]
        res['domain'] = {'partner_invoice_id': partner_invoice_id, 'partner_shipping_id': partner_shipping_id, 'partner_id': domain_partner}
        return res
                

class SaleOrderTypology(models.Model):
   _inherit = "sale.order.type"

   inter_company_transactions = fields.Boolean(string='Inter Company Transactions')
   inter_company_transactions_type = fields.Selection([
        ('primary_inter_company', 'Primary'),
        ('secondary_inter_company', 'Secondary'),
    ], string="Inter Company Transactions Type",default='primary_inter_company')

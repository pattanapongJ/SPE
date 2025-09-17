from odoo import models,fields, api,_
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    inter_company_transactions = fields.Boolean(related="order_type.inter_company_transactions")
    inter_so_company = fields.Char(string = "Ref. SO inter company")
    inter_so_company_count = fields.Integer(compute = "_compute_inter_company_count")

    def _compute_inter_company_count(self):
        for rec in self:
            if rec.inter_so_company:
                so_id = self.env['sale.order'].search([('name', '=', rec.inter_so_company)])
                rec.inter_so_company_count = len(so_id)
            else:
                rec.inter_so_company_count = 0

    def button_confirm_inter_com(self):
        if self.inter_company_transactions:
            if not self.partner_ref or self.partner_ref.strip() == "-":
                raise UserError(_("กรุณาระบุเลขที่ Vendor Reference ก่อนกด Confirm PO"))
            self.button_confirm()
            for pick in self.picking_ids.filtered(lambda l: l.state != "cancel"):
                pick.action_assign()
                if pick.state != "assigned":
                    UserError(_("กรุณาตรวจสอบจำนวนสินค้า"))
                for move in pick.move_lines:
                    move.quantity_done = move.product_uom_qty
                button_validate = pick.with_context(skip_immediate = True).with_context(
                    skip_backorder = True).button_validate()
            if self.state in ('done', 'purchase'):
                self.action_create_invoice()
        else:
            self.button_confirm()

    def action_so_inter_company(self):
        so_ids = self.env['sale.order'].search([('name', '=', self.inter_so_company)])
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

class PurchaseOrderTypeInherit(models.Model):
    _inherit = 'purchase.order.type'
    
    inter_company_transactions = fields.Boolean(string='Inter Company Transactions')
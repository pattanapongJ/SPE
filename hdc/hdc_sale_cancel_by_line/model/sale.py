from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import re


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        for line in self.order_line:
            line.cancel_qty = 0.0
        return res
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # line_status = fields.Selection([
    #     ('Draft', 'draft'),
    #     ('Sale', 'sale'),
    #     ('Done', 'done'),
    #     ('Cancel', 'cancel'),
    # ], string='Status')
    # cancel_qty = fields.Float(string='Cancel Qty', digits='Product Unit of Measure',copy=False)
    canceled_by = fields.Many2one('res.users', string="Canceled By", readonly=True)
    canceled_at = fields.Datetime(string="Canceled Date", readonly=True)


    def action_cancel_line(self):
        PickingListLine = self.env['picking.lists.line']
        if self.product_uom_qty <= self.cancel_qty  :
            raise UserError(_("สินค้าหมดไม่สามารถกดยกเลิกได้"))
        else:
            line_ids = []
            if self.move_ids:
                self.move_ids._compute_picking_done_qty()
                move_lines_ids = self.move_ids.filtered(lambda l: l.state not in ('cancel', 'done') and l.picking_code == 'outgoing')
                if not move_lines_ids:
                    raise UserError(_('สินค้าส่งครบแล้วไม่สามารถกดยกเลิกได้'))
                for move in move_lines_ids:
                    pick_location_id = move.location_id.id
                    picking_id_all = PickingListLine.search([('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id)])
                    picking_id_done = picking_id_all.filtered(lambda l: l.state == 'done')
                    product_uom_qty = move.sale_line_id.product_uom_qty - sum(picking_id_done.mapped('qty_done')) - abs(move.sale_line_id.cancel_qty)
                    line_ids.append((0, 0, {
                        'product_id': move.product_id.id,
                        'location_id': move.location_id.id,
                        'pick_location_id': pick_location_id,
                        'cancel_qty': product_uom_qty,
                        'uom_id': move.product_uom.id,
                        'move_id': move.id,
                        'order_line': move.sale_line_id.id,
                        }))
                if line_ids:
                    wizard = self.env["wizard.cancel.so.line"].create({
                        "line_ids": line_ids
                        })
                    action = {
                        'name': 'Cancel Line Item',
                        'type': 'ir.actions.act_window',
                        'res_model': 'wizard.cancel.so.line',
                        'res_id': wizard.id,
                        'view_mode': 'form',
                        "target": "new",
                        }
                    return action
            else:
                raise UserError(_("สินค้าไม่สามารถกดยกเลิกได้"))
            
    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id', 'dis_price','rounding_price','promotion_discount','remain_demand_qty')
    def _compute_amount(self): # (การทำงานล่าสุด 29/08/2025) ใช้อันนี้แทน _compute_amount ของ hdc_promotion_priority 
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.remain_demand_qty
            price_total = price_total - line.promotion_discount
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount) * line.remain_demand_qty
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit * line.remain_demand_qty) - line.promotion_discount - total_dis
            
            if line.rounding_price:
                try:
                    rounding_value = float(line.rounding_price[1:])
                    decimal_precision = self.env['decimal.precision'].precision_get('Sale Rounding')
                    rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
                    
                    if not rounding_pattern.match(line.rounding_price):
                        raise ValidationError(_('Invalid Rounding format : +20 or -20 with up to %d decimal places' % decimal_precision))

                    if line.rounding_price.startswith("+"):
                        price += rounding_value
                    elif line.rounding_price.startswith("-"):
                        price -= rounding_value
                    else:
                        raise ValidationError(_('Invalid Rounding format : +20 or -20'))
                except:
                    raise ValidationError(_('Invalid Rounding format : +20 or -20'))

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
            price_total = taxes['total_excluded']
            if line.tax_id:
                if line.tax_id.price_include:
                    price_total = taxes['total_included']

            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': price_total,
                'price_subtotal': taxes['total_excluded'],
                'dis_price': total_dis,
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

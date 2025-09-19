# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet


class SaleOrder(models.Model):
    _inherit = "sale.order"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_uom_map_ids = fields.Many2many(related="product_id.sale_uom_map_ids")

    @api.onchange("product_id")
    def product_id_change(self):
        result = super().product_id_change()
        if self.product_id:
            product_uom = self.product_id.uom_map_ids.filtered(lambda l: l.is_default_sale == True).mapped("uom_id")
            if product_uom:
                self.product_uom = product_uom[0]
        domain_uom = [("id", "in", self.sale_uom_map_ids.ids)]
        if result and 'domain' in result:
            result['domain']['product_uom'] = domain_uom
        else:
            result = {"domain": {"product_uom": domain_uom}}
        return result

    def convert_uom_factor(self, product=False, qty=0, sale_line_uom=False):

        if not (product and qty and sale_line_uom):
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        base_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_type == "base" and l.product_id.id == product.id
        )
        if not base_map:  # ตรวจว่ามี factor, uom ที่ base มั้ย
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        base_uom = base_map[0].uom_id

        current_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == sale_line_uom.id and l.product_id.id == product.id
        )
        if (
            not current_map or not current_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        factor = current_map[0].factor_base
        product_qty_f = qty * factor

        return (product_qty_f, base_uom)

    def _action_launch_stock_rule(
        self, previous_product_uom_qty=False
    ):  # เอาการทำงานการแปลงหน่วยมาจาก hdc_product_kit เพราะทำ super ไม่ได้ต้องมาทับ ในจังหวะ แปลงหน่วยก่อนออก return
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != "sale" or not line.product_id.type in ("consu", "product"):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if (
                float_compare(qty, line.product_uom_qty, precision_digits=precision)
                >= 0
            ):
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env["procurement.group"].create(
                    line._prepare_procurement_group_vals()
                )
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update(
                        {"partner_id": line.order_id.partner_shipping_id.id}
                    )
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({"move_type": line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            addition = self.env["addition.operation.type"].search(
                [("code", "=", "AO-02")], limit=1
            )
            product_qty = line.product_uom_qty
            if line.order_id.type_id.is_borrow:
                # if addition:
                #     picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
                #     if picking_type:
                # picking = self.env["stock.picking"].search([("sale_borrow", "=", line.order_id.id),("picking_type_id", "in", picking_type.ids)])
                # move = self.env["stock.move"].search(
                #     [("product_id", "=", line.product_id.id),
                #      ("picking_id", "in", picking.ids), ("state", "!=", "cancel")])
                # sum_qty = sum(move.mapped("product_uom_qty"))
                total_delivered = 0
                if line.borrow_qty > 0:
                    total_delivered = line.borrow_qty - line.return_qty
                    # if total_delivered >=0:
                    #     qty += total_delivered
                # product_uom_qty = line.product_uom_qty - sum_qty + line.return_qty
                product_uom_qty = line.product_uom_qty - total_delivered
                if product_uom_qty < 0:
                    product_uom_qty = 0
                product_qty = product_uom_qty
            else:
                product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            # product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            # ใช้ product_qty และ procurement_uom ใหม่ โดยแปลงจาก product map uom -> factor

            # convert_uom_factor
            product_qty_f, procurement_uom_f = line.convert_uom_factor(
                line.product_id, line.product_uom_qty, line.product_uom
            )

            if not product_qty_f or not procurement_uom_f:  # ไม่สำเร็จ ใช้แบบเดิม
                product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                    product_qty, quant_uom
                )
            else:
                product_qty = product_qty_f
                procurement_uom = procurement_uom_f

            product_bom = line.env["mrp.bom"].search(
                [
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                    ("type", "=", "normal"),
                ],
                limit=1,
            )
            if (
                not line.order_id.type_id.modern_trade
                and line.product_id.route_ids.filtered(
                    lambda l: l.name == "Manufacture"
                )
                and product_bom
            ):
                for line_bom in product_bom.bom_line_ids:
                    line_bom_uom = line_bom.product_uom_id
                    product_qty_bom = line_bom.product_qty * line.product_uom_qty
                    quant_uom_bom = line_bom.product_id.uom_id
                    product_qty_bom, procurement_uom_bom = (
                        line_bom_uom._adjust_uom_quantities(
                            product_qty_bom, quant_uom_bom
                        )
                    )
                    procurements.append(
                        self.env["procurement.group"].Procurement(
                            line_bom.product_id,
                            product_qty_bom,
                            procurement_uom_bom,
                            line.order_id.partner_shipping_id.property_stock_customer,
                            line_bom.product_id.display_name,
                            line.order_id.name,
                            line.order_id.company_id,
                            values,
                        )
                    )
            else:
                procurements.append(
                    self.env["procurement.group"].Procurement(
                        line.product_id,
                        product_qty,
                        procurement_uom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.product_id.display_name,
                        line.order_id.name,
                        line.order_id.company_id,
                        values,
                    )
                )

        if procurements:
            self.env["procurement.group"].run(procurements)
        return True

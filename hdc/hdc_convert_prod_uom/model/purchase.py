from odoo import _, api, fields, models
from odoo.tools.float_utils import float_compare, float_round


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_uom = fields.Many2one("uom.uom", string="Unit of Measure")
    purchase_uom_map_ids = fields.Many2many(related="product_id.purchase_uom_map_ids")

    @api.onchange("purchase_uom_map_ids")
    def _onchange_purchase_uom_map_ids(self):
        if self.product_id:
            product_uom = self.product_id.uom_map_ids.filtered(lambda l: l.is_default_purchase == True).mapped("uom_id")
            if product_uom:
                self.product_uom = product_uom[0]
        domain_uom = [("id", "in", self.purchase_uom_map_ids.ids)]
        return {"domain": {"product_uom": domain_uom}}

    def convert_uom_factor(self, product=False, qty=0, purchase_line_uom=False):

        if not (product and qty and purchase_line_uom):
            qty = 0
            purchase_line_uom = False
            return qty, purchase_line_uom

        base_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_type == "base" and l.product_id.id == product.id
        )
        if not base_map:  # ตรวจว่ามี factor, uom ที่ base มั้ย
            qty = 0
            purchase_line_uom = False
            return qty, purchase_line_uom

        base_uom = base_map[0].uom_id

        current_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == purchase_line_uom.id
            and l.product_id.id == product.id
        )
        if (
            not current_map or not current_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            purchase_line_uom = False
            return qty, purchase_line_uom

        factor = current_map[0].factor_base
        product_qty_f = qty * factor

        return (product_qty_f, base_uom)

    def _prepare_stock_moves(
        self, picking
    ):  # ไปเอาการทำงานมาจาก hdc_master_key เพราะตอนนี้ยังมีการทำงานอยู่ เลยต้องไป depends แล้วก็เอามา เพื่อให้ทำของเราก่อน
        """Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []

        # ตรวจสอบเงื่อนไขสำหรับ Master Key Service
        new_product_id = self.product_id  # เก็บค่าต้นฉบับของ Product ไว้
        if self.product_id.type == "service" and self.product_id.is_master_key_service:
            bom = self.env["mrp.bom"].search(
                [("master_key_service_id", "=", self.product_id.id)], limit=1
            )
            sale_id = self.env["sale.order"].search(
                [
                    ("purchase_master_key_id", "=", self.order_id.id),
                    ("is_master_key", "=", True),
                ],
                limit=1,
            )
            
            if bom:
                
                dummy = sale_id.receipt_master_key_id.move_ids_without_package.filtered(
                    lambda l: l.product_id.is_master_key_dummy
                )
                if dummy:
                    new_product_id = (
                        sale_id.receipt_master_key_id.move_ids_without_package[
                            0
                        ].product_id
                    )
                else:
                    new_product_id = bom.product_tmpl_id.product_variant_id
            
            if sale_id:
                master_key_products = sale_id.order_line.filtered(lambda l: l.product_id.is_master_key_product)
                if master_key_products:
                    res_master_key = self._prepare_master_key_moves(picking, master_key_products)
                    res.extend(res_master_key)

            if new_product_id.type not in ["product", "consu"]:
                return res

            price_unit = self._get_stock_move_price_unit()
            qty = self._get_qty_procurement()

            move_dests = self.move_dest_ids
            if not move_dests:
                move_dests = self.move_ids.move_dest_ids.filtered(
                    lambda m: m.state != "cancel"
                    and not m.location_dest_id.usage == "supplier"
                )

            if not move_dests:
                qty_to_attach = 0
                qty_to_push = self.product_qty - qty
            else:
                move_dests_initial_demand = new_product_id.uom_id._compute_quantity(
                    sum(
                        move_dests.filtered(
                            lambda m: m.state != "cancel"
                            and not m.location_dest_id.usage == "supplier"
                        ).mapped("product_qty")
                    ),
                    self.product_uom,
                    rounding_method="HALF-UP",
                )
                qty_to_attach = min(self.product_qty, move_dests_initial_demand) - qty
                qty_to_push = self.product_qty - move_dests_initial_demand

            if (
                float_compare(
                    qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding
                )
                > 0
            ):
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(
                    qty_to_attach, new_product_id.uom_id
                )
                move_vals = self._prepare_stock_move_vals(
                    picking, price_unit, product_uom_qty, product_uom
                )
                move_vals["product_id"] = new_product_id.id  # ใช้ product ใหม่ใน move
                res.append(move_vals)

            if (
                float_compare(
                    qty_to_push, 0.0, precision_rounding=self.product_uom.rounding
                )
                > 0
            ):
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(
                    qty_to_push, new_product_id.uom_id
                )
                extra_move_vals = self._prepare_stock_move_vals(
                    picking, price_unit, product_uom_qty, product_uom
                )
                extra_move_vals["product_id"] = (
                    new_product_id.id
                )  # ใช้ product ใหม่ใน move
                extra_move_vals["move_dest_ids"] = False  # don't attach
                res.append(extra_move_vals)

            return res

        else:
            if self.product_id.type not in ["product", "consu"]:
                return res

            price_unit = self._get_stock_move_price_unit()
            qty = self._get_qty_procurement()

            move_dests = self.move_dest_ids
            if not move_dests:
                move_dests = self.move_ids.move_dest_ids.filtered(
                    lambda m: m.state != "cancel"
                    and not m.location_dest_id.usage == "supplier"
                )

            if not move_dests:
                qty_to_attach = 0
                qty_to_push = self.product_qty - qty
            else:
                move_dests_initial_demand = self.product_id.uom_id._compute_quantity(
                    sum(
                        move_dests.filtered(
                            lambda m: m.state != "cancel"
                            and not m.location_dest_id.usage == "supplier"
                        ).mapped("product_qty")
                    ),
                    self.product_uom,
                    rounding_method="HALF-UP",
                )
                qty_to_attach = min(self.product_qty, move_dests_initial_demand) - qty
                qty_to_push = self.product_qty - move_dests_initial_demand

            if (
                float_compare(
                    qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding
                )
                > 0
            ):
                # new_product_uom_qty and new_product_uom
                new_product_uom_qty, new_product_uom = self.convert_uom_factor(
                    self.product_id, qty_to_attach, self.product_uom
                )
                if not new_product_uom_qty or not new_product_uom:
                    product_uom_qty, product_uom = (
                        self.product_uom._adjust_uom_quantities(
                            qty_to_attach, self.product_id.uom_id
                        )
                    )
                else:
                    product_uom_qty = new_product_uom_qty
                    product_uom = new_product_uom

                res.append(
                    self._prepare_stock_move_vals(
                        picking, price_unit, product_uom_qty, product_uom
                    )
                )
            if (
                float_compare(
                    qty_to_push, 0.0, precision_rounding=self.product_uom.rounding
                )
                > 0
            ):
                # new_product_uom_qty and new_product_uom
                new_product_uom_qty, new_product_uom = self.convert_uom_factor(
                    self.product_id, qty_to_push, self.product_uom
                )
                if not new_product_uom_qty or not new_product_uom:
                    product_uom_qty, product_uom = (
                        self.product_uom._adjust_uom_quantities(
                            qty_to_push, self.product_id.uom_id
                        )
                    )
                else:
                    product_uom_qty = new_product_uom_qty
                    product_uom = new_product_uom

                extra_move_vals = self._prepare_stock_move_vals(
                    picking, price_unit, product_uom_qty, product_uom
                )
                extra_move_vals["move_dest_ids"] = False  # don't attach
                res.append(extra_move_vals)
            return res

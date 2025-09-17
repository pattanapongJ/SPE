# Copyright 2017 ForgeFlow S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("order_line")
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in sale order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new sale order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for sale in self:
            sale.max_line_sequence = max(sale.mapped("order_line.sequence") or [0]) + 1

    max_line_sequence = fields.Integer(
        string="Max sequence in lines", compute="_compute_max_line_sequence", store=True
    )

    def _reset_sequence(self):
        for order in self:
            current_sequence = 1
            max_sequence = 0
            global_discount_line = None

            for line in sorted(order.order_line, key=lambda x: (x.sequence, x.id)):
                global_discount_id = order.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
                global_discount = order.env["product.product"].search([("id", "=", global_discount_id)],limit=1)
                if line.product_id == global_discount:
                    #โค็ดสำหรับดักเคสกรณี global_discount seq
                    global_discount_line = line
                    continue  

                if line.sequence2 != current_sequence:
                    line.sequence2 = current_sequence

                if not line.display_type:
                    current_sequence += 1

                max_sequence = max(max_sequence, line.sequence2)

            if global_discount_line:
                global_discount_line.sequence = order.max_line_sequence
                global_discount_line.sequence2 = max_sequence + 1

    def write(self, line_values):
        res = super(SaleOrder, self).write(line_values)
        global_discount_id = self.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
        global_discount = self.env["product.product"].search([("id", "=", global_discount_id)],limit=1)
        global_discount_product = global_discount if global_discount else False
        #โค็ดสำหรับดักเคสกรณี global_discount seq

        if 'global_discount_update' in line_values:
            if global_discount_product:
                old_lines = self.mapped("order_line")
                check_global_discount_line = []
                for line in old_lines:
                    if line.product_id == global_discount_product:
                        check_global_discount_line.append(line.id)
                        line.write({'price_unit': -float(line_values.get("global_discount_update"))})

        if 'order_line' in line_values:
            if global_discount_product:
                old_lines = self.mapped("order_line")
                check_global_discount_line = []
                for line in old_lines:
                    if line.product_id == global_discount_product:
                        check_global_discount_line.append(line.id)
                        line.write({'price_unit': -self.global_discount_total})

        if 'global_discount' in line_values:
            if line_values.get('global_discount'):
                gdt_line = self._global_discount_total_line(line_values['global_discount'])

                if global_discount_product:
                    old_lines = self.mapped("order_line")
                    check_global_discount_line = []
                    for line in old_lines:
                        if line.product_id == global_discount_product:
                            check_global_discount_line.append(line.id)
                            line.write({'price_unit': -gdt_line})
                    company_id = self.env.company.id
                    taxes_ids = global_discount_product.taxes_id.filtered(lambda tax: tax.company_id.id == company_id).ids
                    if not check_global_discount_line:
                        description = global_discount_product.description_sale if global_discount_product.description_sale else "-"
                        order_line_values = {
                            'order_id': self.id,
                            'product_id': global_discount_product.id,
                            'name': description,
                            'product_uom_qty': 1,
                            'product_uom': global_discount_product.uom_id.id,
                            'price_unit': -gdt_line,
                            'is_global_discount': True,
                            'tax_id': [(6, 0, taxes_ids)] if taxes_ids else False
                        }
                        order_line = self.env['sale.order.line'].create(order_line_values)
                        if order_line:
                            order_line.sequence = self.max_line_sequence
                            order_line.sequence2 = self.max_line_sequence + 1

            self._compute_tax_id()
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(SaleOrder, self.with_context(keep_line_sequence=True)).copy(
            default
        )
    
    @api.model
    def create(self, values):
        result = super(SaleOrder, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        #โค็ดสำหรับดักเคสกรณี global_discount seq
        if result.global_discount:
            global_discount_id = self.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
            global_discount = self.env["product.product"].search([("id", "=", global_discount_id)],limit=1)
            global_discount_product = global_discount if global_discount else False

            if global_discount_product:
                if result.order_line:
                    existing_line = result.order_line.filtered(lambda line: line.product_id == global_discount_product)
                    if existing_line:
                        return result
                    description = global_discount_product.description_sale if global_discount_product.description_sale else "-"
                    company_id = self.env.company.id
                    taxes_ids = global_discount_product.taxes_id.filtered(lambda tax: tax.company_id.id == company_id).ids
                    order_line_values = {
                        'order_id': result.id,
                        'product_id': global_discount_product.id,
                        'name': description,
                        'product_uom_qty': 1,
                        'product_uom': global_discount_product.uom_id.id,
                        'price_unit': -result.global_discount_total,
                        'is_global_discount': True,
                        'tax_id': [(6, 0, taxes_ids)] if taxes_ids else False
                    }
                    order_line = self.env['sale.order.line'].create(order_line_values)
                    if order_line:
                        order_line.sequence = self.max_line_sequence
                        order_line.sequence2 = self.max_line_sequence + 1
        
            result._compute_tax_id()
        result._reset_sequence()
        return result

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # re-defines the field to change the default
    sequence = fields.Integer(
        help="Gives the sequence of this line when displaying the sale order.",
        default=9999,
        string="Sequence",
    )

    # displays sequence on the order line
    sequence2 = fields.Integer(
        help="Shows the sequence of this line in the sale order.",
        # related="sequence",
        string="No",
        readonly=True,
    )

    @api.model
    def create(self, values):
        line = super(SaleOrderLine, self).create(values)
        # We do not reset the sequence if we are copying a complete sale order
        if self.env.context.get("keep_line_sequence"):
            line.order_id._reset_sequence()
        return line
    


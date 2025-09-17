# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class WizardCreateSaleOrder(models.TransientModel):
    _name = 'wizard.create.sale.order'
    _description = 'Wizard to create sale order'

    quotation_id = fields.Many2one('quotation.order', string = 'Quotations')
    order_line = fields.One2many('wizard.create.sale.order.line', 'wizard_quotation_id', string = 'Product List')
    selected = fields.Boolean(string = "Select All")

    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            for line in self.order_line:
                line.selected = True
        else:
            for line in self.order_line:
                line.selected = False
    @api.model
    def default_get(self, fields):
        res = super(WizardCreateSaleOrder, self).default_get(fields)
        records = self.env['wizard.create.sale.order'].search([])
        lines = [(0, 0, {'record_id': rec.id}) for rec in records]
        res.update({'order_line': lines})
        return res

    def action_confirm(self):
        select_quotation_line = self.order_line.filtered(lambda l: l.selected)
        quotation_id = self.quotation_id
        quotation_line = []
        for lines in select_quotation_line:
            line = lines.quotation_line
            quotation_line.append((0, 0, {
                'name': line.name, 'price_unit': lines.price_unit, 'tax_id': line.tax_id.ids,
                'product_id': line.product_id.id, 'product_template_id': line.product_template_id.id,
                'product_uom_qty': lines.product_uom_qty, 'product_uom': lines.product_uom.id,
                'product_uom_category_id': line.product_uom_category_id.id,
                'product_no_variant_attribute_value_ids': line.product_no_variant_attribute_value_ids.ids,
                'display_type': line.display_type, 'triple_discount': line.triple_discount,
                'rounding_price': line.rounding_price, 'is_global_discount': line.is_global_discount,
                "external_customer": line.external_customer.id if line.external_customer else False,
                "external_item": line.external_item,
                "barcode_customer": line.barcode_customer,
                "barcode_modern_trade": line.barcode_modern_trade,
                "description_customer": line.description_customer,
                "modify_type_txt": line.modify_type_txt,
                "plan_home": line.plan_home,
                "room": line.room,
                }))
        quotation = {
            'order_line': quotation_line, 'quotation_id': quotation_id.id,
            'default_product_global_discount': quotation_id.default_product_global_discount.id, 'origin': quotation_id.origin,
            'client_order_ref': quotation_id.client_order_ref, 'reference': quotation_id.reference, 'date_order': quotation_id.date_order,
            'validity_date': quotation_id.validity_date, 'require_signature': quotation_id.require_signature,
            'require_payment': quotation_id.require_payment, 'partner_id': quotation_id.partner_id.id,
            'partner_invoice_id': quotation_id.partner_invoice_id.id, 'partner_shipping_id': quotation_id.partner_shipping_id.id,
            'pricelist_id': quotation_id.pricelist_id.id, 'currency_id': quotation_id.currency_id.id, 'note': quotation_id.note,
            'payment_term_id': quotation_id.payment_term_id.id, 'fiscal_position_id': quotation_id.fiscal_position_id.id,
            'company_id': quotation_id.company_id.id, 'team_id': quotation_id.team_id.id, 'signature': quotation_id.signature,
            'signed_by': quotation_id.signed_by, 'signed_on': quotation_id.signed_on, 'commitment_date': quotation_id.commitment_date,
            'show_update_pricelist': quotation_id.show_update_pricelist, 'customer_po': quotation_id.customer_po,
            'total_discount': quotation_id.total_discount, 'global_discount': quotation_id.global_discount,
            'global_discount_update': quotation_id.global_discount_update, 'priority': quotation_id.priority,
            'delivery_time': quotation_id.delivery_time.id, 'delivery_terms': quotation_id.delivery_terms.id,
            'offer_validation': quotation_id.offer_validation.id, 'sale_spec': quotation_id.sale_spec.id,
            'user_sale_agreement': quotation_id.user_sale_agreement.id, 'user_id': quotation_id.user_id.id,
            'sale_manager_id': quotation_id.sale_manager_id.id, 'modify_type_txt': quotation_id.modify_type_txt,
            'plan_home': quotation_id.plan_home, 'requested_ship_date': quotation_id.requested_ship_date,
            'requested_receipt_date': quotation_id.requested_receipt_date, 'delivery_trl': quotation_id.delivery_trl.id,
            'customer_contact_date': quotation_id.customer_contact_date, 'delivery_company': quotation_id.delivery_company.id,
            'remark': quotation_id.remark, 'type_id': quotation_id.type_id.id, 'billing_period_id': quotation_id.billing_period_id.id,
            'billing_route_id': quotation_id.billing_route_id.id, 'blanket_order_id': quotation_id.blanket_order_id.id,
            'contact_person': quotation_id.contact_person.id, 'warehouse_id': quotation_id.warehouse_id.id,
            'po_date': quotation_id.po_date,'payment_method_id': quotation_id.payment_method_id.id, 'branch_id': quotation_id.branch_id.id,
            }

        sale_id = self.env['sale.order'].create(quotation)
        action = {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_id.id, 'view_mode': 'form',
            }
        return action

class WizardCreatesSaleOrderLine(models.TransientModel):
    _name = 'wizard.create.sale.order.line'
    _description = 'Wizard to create sale order line'

    wizard_quotation_id = fields.Many2one('wizard.create.sale.order', string = 'Quotations')
    quotation_line = fields.Many2one('quotation.order.line', string = 'Quotations line')
    product_id = fields.Many2one(related='quotation_line.product_id', string = 'Product')
    selected = fields.Boolean(string="Select")
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float('Unit Price', required = True, digits = 'Product Price', default = 0.0)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Text(string='Description', required=True)

    modify_type_txt = fields.Char(string="แปลง/Type/Block") 
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string="ชั้น/ห้อง")
    external_customer = fields.Many2one('res.partner', string="External Customer",domain=[('customer','=',True)])
    external_item = fields.Char(string="External Item")
    barcode_customer = fields.Char(string="Barcode Customer")
    barcode_modern_trade = fields.Char(string="Barcode Product")
    description_customer = fields.Text(string="External Description")

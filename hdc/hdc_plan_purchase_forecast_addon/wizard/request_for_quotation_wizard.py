from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class RequestForQuotationWizard(models.TransientModel):
    _name = "request.for.quotation.wizard"
    _description = "Request For Quotation Wizard"

    name = fields.Char(string="Request For Quotation Wizard", readonly=True, default='Request For Quotation Wizard')
    search_id = fields.Many2one("search.forecast.purchase")
    company_id = fields.Many2one('res.company', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    order_type = fields.Many2one(
        comodel_name="purchase.order.type",
        readonly=False,
        # states=Purchase.READONLY_STATES,
        string="PO Type",
        ondelete="restrict",
        domain="[('company_id', 'in', [False, company_id])]",
    )


    def confirm_create_action(self):
        order_line = []
        purchase_model = self.env['purchase.order']
        if self.order_type and self.order_type.sequence_id:
            name = self.order_type.sequence_id.next_by_id()  # ดึงลำดับจาก sequence
        else:
            name = 'New'  # ใช้ค่าเริ่มต้นเป็น 'New'

        purchase_id = purchase_model.create({
            'name': name,
            'partner_id': self.partner_id.id,
            'order_type': self.order_type.id,
        })
        for product_line in self.search_id.product_line_ids:
            if product_line.selected:
                line = (0, 0, {
                    'product_id': product_line.product_id.id,
                    'name': product_line.product_id.display_name,
                    'product_qty': product_line.rfq_qty,
                    'product_uom': product_line.product_id.uom_id.id,
                })
                order_line.append(line)
        purchase_id.write({
            'order_line': order_line
        })      
        action = {
            'name': "Requests for Quotation",
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'res_id': purchase_id.id,
        }
        return action
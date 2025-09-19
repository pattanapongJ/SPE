from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class WizardAddProductCrr(models.TransientModel):
    _name = "wizard.add.product.crr"
    _description = "Wizard Add Product CRR"

    return_request_id = fields.Many2one(comodel_name="customer.return.request")
    product_line_ids = fields.One2many('wizard.add.product.crr.line', 'wiz_id')
    spe_invoice = fields.Many2one(
        'account.move',
        string="SPE Invoice",
        domain="[('id', 'in', available_invoice_ids), ('state', '=', 'posted')]"
    )
    
    available_invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_available_invoices',
        store=False
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
    )
    company_chain_id = fields.Many2one('company.chain',string='Company Chain',copy=False)
    
    @api.depends('spe_invoice')
    def _compute_available_invoices(self):
        for rec in self:
            partner_id = rec.return_request_id.partner_id
            if partner_id.parent_id:
                partner_id |= partner_id.parent_id
            domain = [('form_no', '!=', False),('partner_id', 'in', partner_id.ids)]
            if rec.spe_invoice:
                domain = ['|'] + domain + [
                    ('form_no', '=', rec.spe_invoice.form_no),
                    ('old_spe_invoice', '=', rec.spe_invoice.form_no),
                    ('partner_id', 'in', partner_id.ids),
                ]
            rec.available_invoice_ids = self.env['account.move'].search(domain).ids

    @api.onchange('spe_invoice')
    def _onchange_spe_invoice(self):
        if not self.spe_invoice:
            self.product_line_ids = [(5, 0, 0)]  # Clear One2many
            return

        existing_product_ids = self.product_line_ids.mapped('product_id').ids
        new_lines = []

        for line in self.spe_invoice.invoice_line_ids.filtered(lambda a: a.product_id.type == 'product' and a.product_id):
            product = line.product_id
            if not product or product.id in existing_product_ids:
                continue

            new_lines.append((0, 0, {
                'product_id': product.id,
                'name': product.display_name,
                'receive_qty': line.quantity,
                'uom': product.uom_id.id,
            }))

        self.product_line_ids = [(5, 0, 0)] + new_lines 

    def action_add_product(self):
        product_list = []
        
        for product_line in self.return_request_id.return_request_lines:
            product_list.append(product_line.product_id.id)

        for line in self.product_line_ids:
            if line.product_id.id not in product_list:
                new_product_line = self.env['customer.return.request.line'].create({
                        'return_request_id':self.return_request_id.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'receive_qty': line.receive_qty,
                        'uom': line.uom.id,
                    })
            elif line.product_id.id in product_list:
                product_line = self.return_request_id.return_request_lines.filtered(
                    lambda a: a.product_id.id == line.product_id.id
                )
                product_line.receive_qty = product_line.receive_qty + line.receive_qty
                old_description = product_line.name.split(',')
                new_description = line.name
                if new_description not in old_description:
                    product_line.name = product_line.name + ','+ line.name

        new_picking = self.env['stock.picking'].create({
                            'partner_id': self.return_request_id.partner_id.id,
                            'picking_type_id': self.return_request_id.picking_type_id.id,
                            'state': 'draft',
                            'origin': self.return_request_id.name,
                            'location_id': self.return_request_id.picking_type_id.default_location_src_id.id,
                            'location_dest_id': self.return_request_id.picking_type_id.default_location_dest_id.id,
                            'note': self.return_request_id.remark,
                            'customer_requisition': self.return_request_id.customer_requisition,
                            })
        for line in self.product_line_ids:  # วนลูปสำหรับสินค้าแต่ละรายการ
                move = self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.receive_qty,  # จำนวนสินค้า
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': self.return_request_id.picking_type_id.default_location_src_id.id,
                    'location_dest_id': self.return_request_id.picking_type_id.default_location_dest_id.id,
                    'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                    'origin': self.return_request_id.name,
                    'state': 'draft',
                    'company_id': self.return_request_id.picking_type_id.company_id.id,
                })

class WizardAddProductCrrLine(models.TransientModel):
    _name = "wizard.add.product.crr.line"
    _description = "Wizard Add Product CRR Line"

    wiz_id = fields.Many2one("wizard.add.product.crr")
    external_product_id = fields.Many2one('multi.external.product',string="External Item")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Text(string="Description")
    receive_qty = fields.Float(string="Receive")
    uom = fields.Many2one(comodel_name="uom.uom", string="UOM", required=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        self.name = self.product_id.display_name
        self.uom = self.product_id.uom_id.id

    @api.onchange('external_product_id')
    def external_product_id_change(self):
        for rec in self:
            if rec.external_product_id:
                product_tmpl_id = rec.external_product_id.product_tmpl_id
                if product_tmpl_id and product_tmpl_id.product_variant_ids:
                    rec.product_id = product_tmpl_id.product_variant_ids[0].id
                else:
                    rec.product_id = False
            else:
                rec.product_id = False


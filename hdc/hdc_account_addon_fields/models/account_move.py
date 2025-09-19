# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import re


class AccountJournal(models.Model):
    _inherit = "account.journal"

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        domain="[('company_id', '=', company_id)]",
    )

class AccountMove(models.Model):
    _inherit = "account.move"

    trip_no = fields.Char(string="Trip No.")
    ps_order = fields.Char(string="PS Order")
    parent_company = fields.Many2one("res.partner",string="Parent Company")

    remark_customer = fields.Text(string="Remark Customer")
    invoice_date = fields.Date(
        string='Invoice/Bill Date',
        readonly=True,
        index=True,
        copy=False,
        default=fields.Date.context_today,
        states={'draft': [('readonly', False)]}
    )

    result_product_sample = fields.Boolean("Result",default=False)
    description_product_sample = fields.Char("Description")

    check_product_sample = fields.Boolean(
        string="Check Product Sample",
        compute="_compute_check_product_sample",
        store=False
    )

    @api.depends('journal_id.type', 'journal_id.sale_example')
    def _compute_check_product_sample(self):
        for rec in self:
            if rec.journal_id.type == 'sale' and rec.journal_id.sale_example:
                rec.check_product_sample = True
            else:
                rec.check_product_sample = False

    @api.onchange('journal_id')
    def _onchange_journal_default_prefix(self):
        options = self.env["ir.sequence.option.line"].get_model_options(self._name)
        if options:
            for rec in self.filtered(lambda l: l.state == "draft"):
                sequences = self.env["ir.sequence.option.line"].get_sequence(rec, options=options)
                # ตรวจสอบว่ามีหลาย sequence หรือไม่
                if len(sequences) > 1:
                    # ดึง sequence ตัวล่าสุด (เรียงตามวันที่สร้าง)
                    sequence = sequences.sorted('create_date', reverse=True)[0]
                else:
                    sequence = sequences

                rec.form_no = ""
                if sequence:
                    prefix = sequence.prefix
                    # ใช้ Regular Expression เพื่อดึงเฉพาะตัวอักษรข้างหน้าชุดแรก
                    match = re.match(r'^[A-Z]+', prefix)
                    if match:
                        rec.form_no = match.group(0)

    @api.onchange('move_type')
    def _onchange_move_type(self):
        if self.move_type in ['in_invoice', 'in_refund']:
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        if self.move_type in ['out_invoice', 'out_refund']:
            return {'domain': {'partner_id': [('customer', '=', True)],'partner_shipping_id': [('customer', '=', True)]}}
        else:
            return {'domain': {'partner_id': []}}
    

    partner_shipping_id = fields.Many2one(
        'res.partner',
        string='Delivery Address',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Delivery address for current invoice."
    )

    form_label_type = fields.Selection(
        selection=[
            ('label', 'Label'),
            ('name', 'Name'),
            ('ref_name', 'Reference + Label'),
            ('barcode_name', 'Barcode + Label'),
            ('external_code_name', 'External Code + External Name'),
            # ('external_desc_name', 'External Description'),
        ],
        string="Form Label",
        required=True,
        default='label',
    )
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    modify_type_txt = fields.Char(string="แปลง/Type/Block") 
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string="ชั้น/ห้อง")
    
    external_product_id = fields.Many2one('multi.external.product',string="External Product")
    external_customer = fields.Many2one('res.partner', string="External Customer",store=True)
    external_item = fields.Char(string="External Item",store=True)
    barcode_customer = fields.Char(string="Barcode Customer",store=True)
    barcode_modern_trade = fields.Char(string="Barcode Product",store=True)
    description_customer = fields.Text(string="External Description",store=True)

    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')
    internal_reference = fields.Char(string="Internal Reference", related='product_id.default_code', store=True)


    @api.onchange('product_id','product_id.product_tmpl_id','move_id.partner_id','product_uom_id')
    def _onchange_external_product(self):
        if self.product_id.product_tmpl_id and self.move_id.partner_id:
            external_product = self.env['multi.external.product'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('partner_id', '=', self.move_id.partner_id.id),
                # ('uom_id', '=', self.product_id.uom_id.id)
            ], limit=1)

            if not external_product:
                external_product = self.env['multi.external.product'].search([
                    ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                    ('company_chain_id', '=', self.move_id.partner_id.company_chain_id.id),
                    # ('uom_id', '=', self.product_id.uom_id.id)
                ], limit=1)

            self.external_product_id = external_product.id if external_product else False
            if self.external_product_id:
                barcode_modern_trade_ids = self.external_product_id.barcode_spe_ids.filtered(lambda x: x.uom_id == self.product_uom_id)
                if barcode_modern_trade_ids:
                    barcode_modern_trade = barcode_modern_trade_ids[0].barcode_modern_trade
                else:
                    barcode_modern_trade = False

                self.external_item = self.external_product_id.name
                self.barcode_customer = self.external_product_id.barcode_modern_trade
                # self.barcode_modern_trade = self.external_product_id.barcode_modern_trade
                self.barcode_modern_trade = barcode_modern_trade
                self.description_customer = self.external_product_id.product_description
            else:
                self.external_item = False
                self.barcode_customer = False
                self.barcode_modern_trade = False
                self.description_customer = False
# -*- coding: utf-8 -*-

from odoo import api,models, fields
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    form_no = fields.Char(string="SPE Invoice")
    old_spe_invoice = fields.Char(string="Old SPE Invoice")
    is_no_spe_invoice = fields.Boolean(related='sale_type_id.is_no_spe_invoice',string='No SPE Invoice',store=True)

    def action_post(self):
        for record in self:
            if not record.sale_type_id.is_no_spe_invoice:
                if record.form_no and record.move_type in ['out_invoice','out_refund'] and record.search_count([('form_no', '=', record.form_no),('state','not in',['draft','cancel']), ('id', '!=', record.id)]) > 0:
                    raise ValidationError("The SPE Invoice must be unique. The value '%s' is already used." % record.form_no)
        return super().action_post()
    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     rgs = args or []
    #     domain = []
    #     vaule = []
    #     if name:
    #         search_terms = name.split(',')  # แยกคำค้นหาตามคอมม่า
    #         res = self.search(domain, limit = limit)
    #         for term in search_terms:
    #             term = (term.strip()).lower()  # ตัดช่องว่างที่ไม่จำเป็น เปลี่ยนข้อความที่ต้องการค้นหาเป็นตัวพิมพ์เล็กทั้งหมด
    #             res = res.filtered(lambda l: term in (l.name or '').lower() or term in (l.form_no or '').lower()    
    #                                          or term in (l.old_spe_invoice or '').lower())
    #         return res.name_get()
    #     return self.search(domain, limit = limit).name_get()
    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("form_no", "=ilike", name + "%"), ("name", operator, name)]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()
    
    @api.depends("name", "form_no")
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.form_no:
                name = f"{name} ({record.form_no})"
            result.append((record.id, name))
        return result

class DistributionDeliveryNoteLine(models.Model):
    _inherit = "distribition.invoice.line"

    spe_invoice = fields.Char(string = "SPE Invoice No",related = 'invoice_id.form_no')
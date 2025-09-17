# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class CertificateResPartner(models.Model):
    _inherit = "res.partner"

    company_chain_id = fields.Many2one('company.chain',string='Company Chain',copy=False)

class CompanyChain(models.Model):
    _name = "company.chain"
    _description = "Company Chain"

    code = fields.Text(translate=True)
    name = fields.Char(translate=True,required=True)
    description = fields.Text(translate=True)

    number_company_chain = fields.Integer(string="Customers", compute="_count_company_chain")

    @api.depends("name")
    def _count_company_chain(self):
        for line in self:
            if line.id:
                line.number_company_chain = self.env['res.partner'].search_count([('company_chain_id', '=', line.id)])
            else:
                line.number_company_chain = 0

    def company_chain_customer(self):
        self.ensure_one()
        partners = self.env['res.partner'].search([('company_chain_id', '=', self.id)]).ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Customers"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "target": "current",       
            "domain": [('id', 'in', partners)]     
        }

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         # ตรวจสอบว่ามีค่าทั้ง name และ code
    #         rec_name = f"{record.name} ({record.code})" if record.code else record.name
    #         result.append((record.id, rec_name))
    #     return result

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class Pricelist(models.Model):
    _inherit = "product.pricelist"
    _description = "Pricelist"


    pricelist_all = fields.Boolean(string='Active Pricelist All')
    partner_id = fields.Many2one('res.partner', string='partner', copy=False)
    customer_lists = fields.Integer(compute="_compute_customer_lists")
    
    group_id = fields.Many2one(
        'pricelist.groups',
        string='Group',
        help="Pricelist Group",
        
    )
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, default=lambda self: self.env.user, )
    sale_team_id = fields.Many2many(
        'crm.team',
        string='Sale Team',
        help="Sale Team linked to this pricelist",
    )


    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices. "
             "The default value comes from the customer.")
    
    user_is_admin = fields.Boolean(default=lambda self: self.env.user.has_group('hdc_pricelist_spe.access_rule_administrator'),compute="_compute_default_user_is_admin")

    approve_below_cost = fields.Boolean(string="Approve Below Cost", default=False)

    def _compute_default_user_is_admin(self):
        for check_admin in self:
            check_admin.user_is_admin = check_admin.env.user.has_group('hdc_pricelist_spe.access_rule_administrator')

    def _compute_customer_lists(self):
        for pricelist in self:
            pricelist.customer_lists = self.env["product.pricelist.customer"].search_count([('pricelist_id', '=', pricelist.id)])
            
    # @api.onchange('user_id')
    # def onchange_user_id(self):
    #     if self.user_id:
    #         return {'domain': {'sale_team_id': [('members', 'in', [self.user_id.id])]}}
    #     else:
    #         return {'domain': {'sale_team_id': []}}

    def action_customer_list(self):
        self.ensure_one()
        context = {
            "default_pricelist_id": self.id,
        }
        return {
            "name": _("Customers"),
            "view_mode": "tree",
            "res_model": "product.pricelist.customer",
            "type": "ir.actions.act_window",
            "context": context,
            "domain": [("pricelist_id", "=", self.id)],
        }    

    @api.constrains('pricelist_all')
    def _check_pricelist_all_unique(self):
        for record in self:
            if record.pricelist_all:
                # ค้นหา pricelist อื่นที่ติ๊ก pricelist_all ไว้
                existing_pricelist = self.search([
                    ('pricelist_all', '=', True),
                    ('id', '!=', record.id)
                ], limit=1)
                
                if existing_pricelist:
                    warning_message = {
                        'title': _("Warning"),
                        'message': _(
                            "กรุณาตรวจสอบ Pricelist ราคากลางอีกครั้ง เนื่องจากมี Pricelist ราคากลางอยู่แล้วใน %s"
                        ) % existing_pricelist.name,
                    }
                    return {'warning': warning_message}
                    
class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    group_id = fields.Many2one( related='pricelist_id.group_id', index=True )
    net_price = fields.Boolean(string='Net Price', index=True,default=False)

    pricelist_cost_price = fields.Float(string="Cost Price", default=0.0)
    
    # เพิ่ม related fields สำหรับแสดง Internal Reference และ Product Name
    product_default_code = fields.Char(
        string='Internal Reference', 
        related='product_tmpl_id.default_code', 
        readonly=True, 
        store=True
    )
    product_name = fields.Char(
        string='Product Name', 
        related='product_tmpl_id.name', 
        readonly=True, 
        store=True
    )
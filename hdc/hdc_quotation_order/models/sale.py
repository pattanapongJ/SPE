# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang
from datetime import datetime, timedelta, date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    quotation_id = fields.Many2one('quotation.order', string = 'Quotation', store=True)
    state = fields.Selection(selection_add = [('draft', 'Waiting for confirm')])

    def action_sale_ok2(self):
        if self.requested_receipt_date:
            self.requested_receipt_date += timedelta(days=4)
        return super(SaleOrder, self).action_sale_ok2()

    # if self.requested_receipt_date:
    #         self.requested_receipt_date += timedelta(days=4)

class ResPartnerIn(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('ref', operator, name), ('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids = self._name_search(name, args, operator, limit=limit)
        return self.browse(ids).sudo().with_context(show_search_name=True).name_get()
    
    def name_get_show_search_name(self):
        name = self.name or ''
        if self.company_name or self.parent_id:
            if not name and self.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[self.type]
            if not self.is_company:
                name = self._get_contact_name(self, name)
        if self.street:
            name = f"{name} {self.street}"
        if self.street2:
            name = f"{name} {self.street2}"
        if self.city:
            name = f"{name} {self.city}"
        if self.state_id:
            name = f"{name} {self.state_id.name}"            
        if self.ref:
            name = f"{name} ({self.ref})"
        return name
    
    def name_get(self):
        context = self.env.context or {}
        if context.get('show_search_name'):
            res = []
            for rec in self:
                name = rec.name_get_show_search_name()
                res.append((rec.id, name))
            return res
        else:
            return super(ResPartnerIn, self).name_get()
        
    def _get_name(self):
        name = super()._get_name()
        partner = self
        if self._context.get('show_ref'):
            name_index = name.find(partner.name)
            if name_index != -1:
                before_insert = name[:name_index + len(partner.name)]
                after_insert = name[name_index + len(partner.name):]
                name = f"{before_insert}\n[{partner.ref}]{after_insert}"
        if self._context.get('show_vat') and partner.vat:
            vat_index = name.find(partner.vat)
            if vat_index != -1:
                before_insert = name[:vat_index]
                after_insert = name[vat_index:]
                name = f"{before_insert}Tax ID {after_insert}"
        if self._context.get('show_name_only'):
            name = partner.name
        return name
        
        

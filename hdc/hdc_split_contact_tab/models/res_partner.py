# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # delivery_line = fields.Many2one("delivery.round", "Delivery Line", domain=[('status_active', '=', True)])
    firstname = fields.Char("First name", index=True)
    lastname = fields.Char("Last name", index=True)
    contact_person = fields.Char()
    # parent_id = fields.Many2one('res.partner.category', string='Parent Category', index=True, ondelete='cascade')
    # child_contact_ids = fields.One2many('res.partner.category', 'parent_id', string='Child contacts Tags')
    child_contact_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])
    child_delivery_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])
    child_invoice_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])
    child_other_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])
    child_private_ids = fields.One2many('res.partner', 'parent_id', string='Contact', domain=[('active', '=', True)])
# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
from collections import defaultdict

class Quotations(models.Model):
    _inherit = 'quotation.order'

    pdr_id = fields.Many2many('mrp.pdr', string='PDR ID', ondelete='cascade',copy=False)
    state_pdr = fields.Char(string='Active PDR State', compute='_compute_pdr_count')
    check_access_role_pdr = fields.Selection(
        [('main_admin', 'Main Admin'),('admin', 'Admin'),
         ('access', 'Access'),
         ('user', 'Users')],
        compute='_compute_check_access_role_pdr',
        string='Check Access Role',
        # store=True,
        default=lambda self: self._default_check_access_role_pdr(),  # กำหนด default
        copy=False
    )

    @api.depends('check_access_role_pdr')
    def _compute_check_access_role_pdr(self):
        for record in self:
            # แอดมิน
            if self.env.user.has_group('hdc_pr_design_request.group_admin_product_design'):
                record.check_access_role_pdr = 'main_admin'
            # โรงงาน
            elif self.env.user.has_group('hdc_pr_design_request.group_can_edit_product_design'):
                record.check_access_role_pdr = 'admin'
            # ลาดพร้าว
            elif self.env.user.has_group('hdc_pr_design_request.group_product_design'):
                record.check_access_role_pdr = 'access'
            else:
                record.check_access_role_pdr = 'user'

    def _default_check_access_role_pdr(self):
        if self.env.user.has_group('hdc_pr_design_request.group_admin_product_design'):
            return 'main_admin'
        if self.env.user.has_group('hdc_pr_design_request.group_can_edit_product_design'):
            return 'admin'
        elif self.env.user.has_group('hdc_pr_design_request.group_product_design'):
            return 'access'
        else:
            return 'user'

    product_line_ids = fields.One2many(
        'pdr.product.list.line', 
        compute='_compute_product_line_ids',
        inverse='_inverse_lines',
        string='Product Lines',
    )

    def _inverse_lines(self):
        """ Little hack to make sure that when you change something on these objects, it gets saved"""
        pass

    pdr_count = fields.Integer(string='PDR Count', compute='_compute_pdr_count', store=True)
    pdr_active_count = fields.Integer(string='PDR Active Count', compute='_compute_pdr_count', store=True)

    @api.depends('pdr_id', 'pdr_id.state')
    def _compute_pdr_count(self):
        for record in self:
            pdr_active = record.pdr_id.filtered(lambda pdr: pdr.state != 'cancel')
            record.pdr_count = len(record.pdr_id)
            record.pdr_active_count = len(pdr_active)
            if pdr_active:
                record.state_pdr = pdr_active[0].state
            else:
                record.state_pdr = 'cancel'

    @api.depends('pdr_id', 'pdr_id.state', 'pdr_id.product_line_ids')
    def _compute_product_line_ids(self):
        for record in self:
            product_lines = self.env['pdr.product.list.line']
            valid_pdrs = record.pdr_id.filtered(lambda pdr: pdr.state != 'cancel')
            for pdr in valid_pdrs:
                product_lines |= pdr.product_line_ids
            record.product_line_ids = product_lines

    def open_product_request_request(self):
        self.ensure_one()
        if not self.pdr_id:
            raise UserError(_("This Quotation does not have a linked Product Design Request (PDR)."))
        if len(self.pdr_id) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Product Design Request',
                'res_model': 'mrp.pdr',
                'view_mode': 'form',
                'res_id': self.pdr_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Product Design Requests',
                'res_model': 'mrp.pdr',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.pdr_id.ids)],
                'target': 'current',
            }

    def create_product_disign_request(self):
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Design Request',
                'res_model': 'mrp.pdr',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_quotation_id': self.id,
                            'default_partner_id':  self.partner_id.id,
                            'default_ref_no':  self.name,
                            },
            }
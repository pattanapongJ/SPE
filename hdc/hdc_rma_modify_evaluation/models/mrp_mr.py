# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _inherit = 'mrp.mr'
    
    repair_product_line_ids = fields.One2many('mr.repair.product.list.line', 'mr_id',tracking=True,copy=True)
    is_repair = fields.Boolean(string='Is Repair',default=False)

class MRRepairProductListLine(models.Model):
    _name = 'mr.repair.product.list.line'
    _description = 'MR Repair Product List Line'

    mr_id = fields.Many2one('mrp.mr', string='mr_id', ondelete='cascade')
    type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')], 'Type', default='add', required=True)
    product_id = fields.Many2one(
        'product.product', 'Product', required=True, check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    name = fields.Text('Description', required=True)
    product_uom_qty = fields.Float(
        'Quantity', default=1.0,
        digits='Product Unit of Measure', required=True)
    product_uom = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        required=True, domain="[('category_id', '=', product_uom_category_id)]")
    company_id = fields.Many2one(
        related='mr_id.company_id', store=True, index=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
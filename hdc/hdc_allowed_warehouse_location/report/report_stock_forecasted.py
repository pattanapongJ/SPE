# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_is_zero, format_datetime, format_date, float_round


class ReplenishmentReport(models.AbstractModel):
    _inherit = 'report.stock.report_product_product_replenishment'

    @api.model
    def get_filter_state(self):
        res = {}
        res['warehouses'] = self.env['stock.warehouse'].search_read(domain= [('id', '=', self.env.user.allowed_warehouse_ids.ids)], fields=['id', 'name', 'code'])
        res['active_warehouse'] = self.env.context.get('warehouse', False)
        # res['allowed_warehouse'] = self.env.user.allowed_warehouse_ids.ids
        if not res['active_warehouse']:
            company_id = self.env.context.get('allowed_company_ids')[0]
            res['active_warehouse'] = self.env['stock.warehouse'].search([('company_id', '=', company_id), ('id', '=', self.env.user.allowed_warehouse_ids.ids)], limit=1).id
        # ('id', 'in', self.env.user.allowed_warehouse_ids.ids)
        return res
    
    def _get_report_data(self, product_template_ids=False, product_variant_ids=False):
        assert product_template_ids or product_variant_ids
        res = {}

        # Get the warehouse we're working on as well as its locations.
        if self.env.context.get('warehouse'):
            warehouse = self.env['stock.warehouse'].browse(self.env.context['warehouse'])
        else:
            warehouse = self.env['stock.warehouse'].search([
                ('company_id', '=', self.env.company.id),('id', '=', self.env.user.allowed_warehouse_ids.ids)
            ], limit=1)
            self.env.context = dict(self.env.context, warehouse=warehouse.id)
        wh_location_ids = [loc['id'] for loc in self.env['stock.location'].search_read(
            [('id', 'child_of', warehouse.view_location_id.id)],
            ['id'],
        )]
        res['active_warehouse'] = warehouse.display_name

        # Get the products we're working, fill the rendering context with some of their attributes.
        if product_template_ids:
            product_templates = self.env['product.template'].browse(product_template_ids)
            res['product_templates'] = product_templates
            res['product_variants'] = product_templates.product_variant_ids
            res['multiple_product'] = len(product_templates.product_variant_ids) > 1
            res['uom'] = product_templates[:1].uom_id.display_name
            res['quantity_on_hand'] = sum(product_templates.mapped('qty_available'))
            res['virtual_available'] = sum(product_templates.mapped('virtual_available'))
        elif product_variant_ids:
            product_variants = self.env['product.product'].browse(product_variant_ids)
            res['product_templates'] = False
            res['product_variants'] = product_variants
            res['multiple_product'] = len(product_variants) > 1
            res['uom'] = product_variants[:1].uom_id.display_name
            res['quantity_on_hand'] = sum(product_variants.mapped('qty_available'))
            res['virtual_available'] = sum(product_variants.mapped('virtual_available'))
        res.update(self._compute_draft_quantity_count(product_template_ids, product_variant_ids, wh_location_ids))

        res['lines'] = self._get_report_lines(product_template_ids, product_variant_ids, wh_location_ids)
        return res
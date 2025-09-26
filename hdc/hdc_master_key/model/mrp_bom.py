# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    master_key_service_id = fields.Many2one('product.product', string='Master Key Service')

    @api.model
    def _bom_find(self, product_tmpl=None, product=None, picking_type=None, company_id=False, bom_type=False):
        if (
            (product and product.type == 'service' and product.is_master_key_service) or 
            (product_tmpl and product_tmpl.type == 'service' and product_tmpl.is_master_key_service)
        ):
            
            domain = self._bom_find_domain(
                product_tmpl=product_tmpl,
                product=product,
                picking_type=picking_type,
                company_id=company_id,
                bom_type=bom_type
            )
            
            if not domain:
                return self.env['mrp.bom']
            
            return self.search(domain, order='sequence, product_id', limit=1)
        
        else:
            return super(MrpBom, self)._bom_find(
                product_tmpl=product_tmpl,
                product=product,
                picking_type=picking_type,
                company_id=company_id,
                bom_type=bom_type
            )



    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids')
    def _check_bom_lines(self):
        for bom in self:
            for bom_line in bom.bom_line_ids:
                # if bom.product_id:
                #     same_product = bom.product_id == bom_line.product_id
                # else:
                #     same_product = bom.product_tmpl_id == bom_line.product_id.product_tmpl_id
                # if same_product:
                #     raise ValidationError(_("BoM line product %s should not be the same as BoM product.") % bom.display_name)
                if bom.product_id and bom_line.bom_product_template_attribute_value_ids:
                    raise ValidationError(_("BoM cannot concern product %s and have a line with attributes (%s) at the same time.")
                        % (bom.product_id.display_name, ", ".join([ptav.display_name for ptav in bom_line.bom_product_template_attribute_value_ids])))
                for ptav in bom_line.bom_product_template_attribute_value_ids:
                    if ptav.product_tmpl_id != bom.product_tmpl_id:
                        raise ValidationError(_(
                            "The attribute value %(attribute)s set on product %(product)s does not match the BoM product %(bom_product)s.",
                            attribute=ptav.display_name,
                            product=ptav.product_tmpl_id.display_name,
                            bom_product=bom_line.parent_product_tmpl_id.display_name
                        ))


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    @api.constrains('product_id', 'move_raw_ids')
    def _check_production_lines(self):
        for production in self:
            if not production.bom_id.master_key_service_id:
                if production.mr_id.is_modify == False:
                    for move in production.move_raw_ids:
                        if production.product_id == move.product_id:
                            raise ValidationError(_("The component %s should not be the same as the product to produce.") % production.product_id.display_name)
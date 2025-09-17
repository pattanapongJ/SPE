# Copyright 2019 C2i Change 2 improve - Eduardo Magdalena <emagdalena@c2i.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    bom_revision = fields.Char(string="Revision")
    check_default = fields.Boolean(string="Default")

    def name_get(self):
        return [(bom.id, 'Rev%s : %s' % (bom.bom_revision or '', bom.product_tmpl_id.display_name)) for bom in self]

    @api.model
    def _bom_find2(self, product_tmpl=None, product=None, picking_type=None, company_id=False, bom_type=False):
        """ Finds BoM for particular product, picking and company """
        if product and product.type == 'service' or product_tmpl and product_tmpl.type == 'service':
            return self.env['mrp.bom']
        domain = self._bom_find_domain(product_tmpl=product_tmpl, product=product, picking_type=picking_type, company_id=company_id, bom_type=bom_type)
        if domain is False:
            return self.env['mrp.bom']
        domain += [('check_default', '=', True)]
        return self.search(domain, order='sequence, product_id', limit=1)

    @api.onchange('check_default')
    def onchange_check_default(self):
        search_self = self.search([('product_tmpl_id', '=', self.product_tmpl_id.id), ('check_default', '=', True)])
        if search_self:
            raise UserError(_("You can set default only one."))


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if not self.product_id:
            self.bom_id = False
        elif not self.bom_id or self.bom_id.product_tmpl_id != self.product_tmpl_id or (
                self.bom_id.product_id and self.bom_id.product_id != self.product_id):
            picking_type_id = self._context.get('default_picking_type_id')
            picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
            bom = self.env['mrp.bom']._bom_find2(product = self.product_id, picking_type = picking_type,
                                                company_id = self.company_id.id, bom_type = 'normal')
            if bom:
                self.bom_id = bom.id
                self.product_qty = self.bom_id.product_qty
                self.product_uom_id = self.bom_id.product_uom_id.id
            else:
                self.bom_id = False
                self.product_uom_id = self.product_id.uom_id.id
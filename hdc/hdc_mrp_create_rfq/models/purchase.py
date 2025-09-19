import operator as py_operator
from ast import literal_eval
from collections import defaultdict

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round


class PurchaseOrderIntherit(models.Model):
    _inherit = "purchase.order"

    is_create_rfq = fields.Boolean(
        string="Is Create RFQ",
        default=False,
    )

    create_rfq_to_mo_count = fields.Integer(
        "Count of generated PO",
        compute='_compute_create_rfq_to_mo_count',
        groups='purchase.group_purchase_user')

    @api.depends('state')
    def _compute_create_rfq_to_mo_count(self):
        for po in self:
            origin = po.origin
            po.create_rfq_to_mo_count = self.env['mrp.production'].search_count([('name', '=', origin)])


    def action_view_create_rfq_to_mo(self):
        self.ensure_one()
        origin = self.origin
        mo_ids = self.env['mrp.production'].search([('name', '=', origin)]).ids
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(mo_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mo_ids[0],
            })
        else:
            action.update({
                'name': _("MRP Production generated from %s", self.name),
                'domain': [('id', 'in', mo_ids)],
                'view_mode': 'tree,form',
            })
        return action
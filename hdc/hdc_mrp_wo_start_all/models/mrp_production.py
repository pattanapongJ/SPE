# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _,api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def button_start(self):
        for rec in self:
            check_material = rec.check_material_availability()
            if check_material is False :
                raise UserError(_("Please check the components for production again."))
            if rec.state in ('confirmed', 'progress'):
                for wo in rec.workorder_ids:
                    wo.button_start()

    def button_done(self):
        for rec in self:
            for wo in rec.workorder_ids:
                if wo.is_user_working:
                    wo.button_finish()

    hide_btn = fields.Boolean(
        compute="_compute_workorder_ids", string="Check Start BTN",default=True
    )

    def check_material_availability(self):
        for production in self:
            check = 0
            for move in production.move_raw_ids:
                if move.reserved_availability != move.product_uom_qty:
                    check +=1
            availiable = True
            if check >0:
                availiable = False
            if production.state not in ('confirmed','progress'):
                availiable = True
            return availiable
    def _compute_workorder_ids(self):
        for mo in self:
            check_all_progress = mo.workorder_ids.filtered(
                    lambda l: l.is_user_working == True
                )
            if mo.state not in ['confirmed','progress'] or (mo.unreserve_visible is False and  mo.state == 'confirmed') or (len(check_all_progress) == len(mo.workorder_ids) and mo.state == 'progress'):
                mo.hide_btn = True
            else:
                mo.hide_btn = False
        




from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError
from datetime import time, datetime, timedelta



class InterTransferOnhandLocation(models.Model):
    _name = 'inter.transfer.onhand.location'

    name = fields.Char(related='company_id.name')
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),index = True,
    )
    location_id = fields.Many2one('stock.location', "Source Location",required=True)
    inter_onhand_location_ids = fields.Many2many('stock.location', string="Inter Transfer Request Onhand Location")
    
    @api.model
    def _default_company_id(self):
        return self.env.company
    
    @api.model
    def create(self, vals):
        company_id = vals.get("company_id")
        location_id = vals.get("location_id")

        if company_id and location_id:
            inter_onhand_location_id = self.search([
                ('company_id', '=', company_id),
                ('location_id', '=', location_id),
            ], limit=1)
            if inter_onhand_location_id:
                raise UserError(_("This company and source location already exists."))

        return super(InterTransferOnhandLocation, self).create(vals)

    def write(self, vals):
        for rec in self:
            company_id = vals.get("company_id", rec.company_id.id)
            location_id = vals.get("location_id", rec.location_id.id)

            inter_onhand_location_id = self.search([
                ('company_id', '=', company_id),
                ('location_id', '=', location_id),
                ('id', '!=', rec.id)
            ], limit=1)

            if inter_onhand_location_id:
                raise UserError(_("This company and source location already exists."))

        return super(InterTransferOnhandLocation, self).write(vals)
        
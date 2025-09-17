from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError
from datetime import time, datetime, timedelta



class MrpOnhandLocation(models.Model):
    _name = 'mrp.mr.onhand.location'

    name = fields.Char(related='company_id.name')
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),index = True,
    )
    mr_onhand_location_ids = fields.Many2many('stock.location', string="MRP Request Onhand Location")
    
    @api.model
    def _default_company_id(self):
        return self.env.company
    
    @api.model
    def create(self, vals):
        if vals.get('company_id'):
            mrp_mr_onhand_location_id = self.env['mrp.mr.onhand.location'].search([('company_id','=',vals.get('company_id'))])
            if mrp_mr_onhand_location_id:
                raise UserError(
                        _(
                            "You have mrp onhand locations on this company"
                        )
                    )
        res = super(MrpOnhandLocation, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('company_id'):
            mrp_mr_onhand_location_id = self.env['mrp.mr.onhand.location'].search([('company_id','=',vals.get('company_id'))])
            if mrp_mr_onhand_location_id:
                raise UserError(
                        _(
                            "You have mrp onhand locations on this company"
                        )
                    )
        res = super(MrpOnhandLocation, self).write(vals)
        return res
        
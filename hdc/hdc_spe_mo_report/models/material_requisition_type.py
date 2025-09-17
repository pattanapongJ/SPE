from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import time, datetime, timedelta



class MaterialRequisitionType(models.Model):
    _name = 'material.requisition.type'

    name = fields.Char(required=True)
    is_default = fields.Boolean("Is Default")

    @api.model
    def create(self, vals):
        if vals.get('is_default') == True:
            material_requisition_type_ids = self.env['material.requisition.type'].search([])
            for m in material_requisition_type_ids:
                m.is_default = False
        res = super(MaterialRequisitionType, self).create(vals)
        return res
    
    def write(self, vals):
        if vals.get('is_default') == True:
            material_requisition_type_ids = self.env['material.requisition.type'].search([])
            for m in material_requisition_type_ids:
                m.is_default = False
        res = super(MaterialRequisitionType, self).write(vals)
        return res
        
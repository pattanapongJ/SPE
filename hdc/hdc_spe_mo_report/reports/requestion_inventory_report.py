
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate
from odoo.tools import format_date

import io
import base64
import xlsxwriter
import re

from datetime import datetime, timedelta
import calendar

class RequestionInventoryReport(models.AbstractModel):
    _name = 'report.hdc_spe_mo_report.hdc_requestion_mo_report'
    _description = 'Requestion Inventory Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        mrp_id_origin = False
        mrp_id = self.env["mrp.production"].search([('id','=',data.get('mrp_id'))])
        docs = self.env['mrp.production'].browse(mrp_id.id)
        operation_id = self.env["mrp.routing.workcenter"].search([('id','=',data['operation_id'])])
        material_requisition_type_id = self.env["material.requisition.type"].search([('id','=',data['material_requisition_type_id'])])
        if mrp_id.origin:
            mrp_id_origin = self.env["mrp.production"].search([('name','=',mrp_id.origin)])
        iso_number = self.env["iso.operation.type"].search([('operation_type_id','=',docs.picking_type_id.id),
                                                            ('doc_name','=','material_requestion')],limit=1)
        report_values = {
            'docs':docs,
            'operation_id': operation_id,
            'mrp_id_origin':mrp_id_origin,
            'material_requisition_type_id':material_requisition_type_id,
            'iso_number': iso_number.iso_number if iso_number else '-',
        }

        return report_values
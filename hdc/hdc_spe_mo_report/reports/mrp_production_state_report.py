
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

class MrpProductionStateReport(models.AbstractModel):
    _name = 'report.hdc_spe_mo_report.hdc_mrp_production_state_report'
    _description = 'Mrp Production State Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        mrp_id_origin = False
        mrp_id = self.env["mrp.production"].search([('id','=',data.get('mrp_id'))])
        docs = self.env['mrp.production'].browse(mrp_id.id)
        mrp_production_state_ids = self.env["mrp.production.state"].search([('mrp_id','=',docs.id)])
        iso_number = self.env["iso.operation.type"].search([('operation_type_id','=',docs.picking_type_id.id),
                                                            ('doc_name','=','mrp_production_state')],limit=1)
        report_values = {
            'docs':docs,
            'mrp_production_state_ids': mrp_production_state_ids,
            'iso_number': iso_number.iso_number if iso_number else '-',
        }

        return report_values
from odoo import api, models, _

from datetime import datetime


class InternalAccountStatement(models.AbstractModel):
    _name = 'report.bs_internal_account_statement_report.report_acc'
    _description = 'Internal Account Statement Report'
    
    @api.model
    def _get_report_values(self, docids, data):
        wizard_id = data['wizard_id']
        date_start = data['date_start']
        date_end = data['date_end']
        company_id = data['company_id']
        partner_id = data['partner_id']
        sale_team_id = data['sale_team_id']

        today = datetime.strftime(datetime.today(), "%d/%m/%Y")
        
        report_result = self._compute_results(partner_id, company_id, date_start=date_start, date_end=date_end)
        
        header_info = self._build_header_info(partner_id)
        
        return {
            "doc_ids": [wizard_id],
            "doc_model": "internal.acc.stmt.report.wizard",
            "docs": self.env["internal.acc.stmt.report.wizard"].browse(wizard_id),
            "date_from": date_start,
            "date_to": date_end,
            "report_result": report_result,
            "report_date": today,
            "header_info": header_info
        }
        
    def _build_header_info(self, partner_id):
        header_info = {}
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        # ---------------- left side
        # 1. name
        p_name = partner.name
        # 2. address
        street = partner.street if partner.street else ''
        street2 = partner.street2 if partner.street2 else ''
        city = partner.city if partner.city else ''
        state = partner.state_id.name if partner.state_id else ''
        zip = partner.zip if partner.zip else ''
        p_address = f"{street} {street2} {city} {state} {zip}"
        # 3. ref
        p_ref = partner.ref
        # 4. remark
        p_remark = partner.internal_remark
        
        # --------------- middle 
        # 1. partner group code
        p_group_code = partner.partner_group_id.code
        # 2. 
        
        
        header_info['partner'] = {
            "name": p_name,
            "address": p_address,
            "ref": p_ref,
            "remark": p_remark,
        }
        
        header_info['middle'] = {
            'p_group_code': p_group_code
        }
        
        return header_info
        
        
    def _compute_results(self, partner_id, company_id, date_start=False, date_end=False):
        pass
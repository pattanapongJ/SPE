from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardQuotationBo(models.TransientModel):
    _name = "wizard.quotation.bo"
    _description = "wizard.quotation.bo"

    date_from = fields.Date('เริ่มต้น',required=True)
    date_to = fields.Date('ถึง',required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    project_name = fields.Many2many('sale.project', string='ชื่อโปรเจค')

    document = fields.Selection([
        ("pdf", "Report"),
        ("excel", "Excel"),
    ],
    string="ประเภท",
    default='pdf'
    )

    def get_report(self):
        domain = [('state', '=', 'draft'), ('date_order', '<=', self.date_to), ('date_order', '>=', self.date_from)]

        if self.project_name:
            project_name_ids = self.project_name.ids
            domain.append(('project_name', 'in', project_name_ids))

        # หาทุกรายการที่ partner_id ยังไม่หาย
        qo_ids = self.env['quotation.order'].search(domain)

        if not qo_ids:
            raise UserError("ไม่พบข้อมูล Quotation Order ที่ตรงตามเงื่อนไข")

        if self.document == 'pdf':
            return self.env.ref('hdc_quotation_order.quotation_project_bo_view').report_action(qo_ids)
        elif self.document == 'excel':
            report = self.env['ir.actions.report'].search([
                ('report_name', '=', 'quotation_project_bo_xlsx'),
                ('report_type', '=', 'xlsx')], limit=1)
            return report.report_action(qo_ids)

        
        
class WizardQuotationDepartment(models.TransientModel):
    _name = "wizard.quotation.department"
    _description = "wizard.quotation.department"

    date_from = fields.Date('เริ่มต้น',required=True)
    date_to = fields.Date('ถึง',required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    department = fields.Many2many('bs.finance.dimension', string='แผนก')

    document = fields.Selection([
        ("pdf", "Report"),
        ("excel", "Excel"),
    ],
    string="ประเภท",
    default='pdf'
    )

    def get_report(self):
        domain = [('state', '=', 'draft'), ('date_order', '<=', self.date_to), ('date_order', '>=', self.date_from)]
        
        if self.department:
            department_ids = self.department.ids  # ดึง ID ของแผนก
            domain.append(('finance_dimension_1_id', 'in', department_ids))  # ใช้ 'in' แทน '='
        
        qo_id = self.env['quotation.order'].search(domain)
        
        if self.document == 'pdf':
            return self.env.ref('hdc_quotation_order.quotation_project_depart_view').report_action(qo_id)
        
        elif self.document == 'excel':
            report = self.env['ir.actions.report'].search(
                [('report_name', '=', 'quotation_project_department_xlsx'),
                ('report_type', '=', 'xlsx')], limit=1)
            return report.report_action(self)
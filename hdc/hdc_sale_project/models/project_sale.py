from odoo import api, models,fields,_
from odoo.exceptions import ValidationError

class SaleProject(models.Model):
    _name = "sale.project"
    _description = 'Sale Project'
    _rec_name = "project_name"
    
    is_customer= fields.Boolean(related='partner_id.is_customer')
    project_name = fields.Char('Project Name')
    code = fields.Char('code',default='PRO')
    partner_id = fields.Many2one('res.partner', string='Customer')
    start_date = fields.Datetime('Start date')
    end_date = fields.Datetime('End date')
    user_id = fields.Many2one('res.users', 'Salesperson')
    status = fields.Selection([('active', 'Active'), 
                               ('archived', 'Archived')], 
                              default='active', string='Status')
    active = fields.Boolean(string ="Active", default=True)

    sale_taker_id = fields.Many2one('hr.employee', string="Sale Taker")
    customer_po_deadline = fields.Date(string="Customer PO Deadline")

    remark_project = fields.Text('Remark ข้อมูลโครงการ')

    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            if record.code:
                existing = self.search([('id', '!=', record.id), ('code', '=', record.code)])
                if existing:
                    raise ValidationError(f'Code "{record.code}" already exists!')

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    project_name = fields.Many2one('sale.project', string='Project Name')
    remark_project = fields.Text('Remark ข้อมูลโครงการ')
    start_date = fields.Datetime('Start date')
    end_date = fields.Datetime('End date')
    sale_spec = fields.Many2one('res.users', string='Sale Spec')
    administrator = fields.Many2one('res.users', string='Administrator', readonly=True, store=True)
    user_id = fields.Many2one("res.users",string="Salesperson",readonly=True,states={"draft": [("readonly", False)]},)

    @api.onchange('team_id')
    def user_id_domain_true(self):        
        return {"domain":{"user_id":[('id','in',self.team_id.member_ids.ids)]}}
        
    @api.onchange('name')
    def _onchange_project_name(self):            
        if self.project_name and self.project_name.remark_project:
            self.remark_project = self.project_name.remark_project
        else:
            self.remark_project = False
        sale_agreement_user = self.env.user
        self.administrator = sale_agreement_user
        self.write({'administrator': sale_agreement_user.id})

    @api.onchange('project_name')
    def _onchange_project_name_to_change_start_end_date(self): 
        self.start_date = self.project_name.start_date
        self.end_date = self.project_name.end_date
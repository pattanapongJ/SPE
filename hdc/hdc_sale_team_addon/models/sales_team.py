from datetime import date

from odoo import api, fields, models, _
from datetime import datetime

class CrmTeam(models.Model):
    _inherit = "crm.team"

    sale_spec_member_ids = fields.One2many(
        'res.users', 'sale_spec_team_id', string='Sale Spec Members',
        check_company=True, domain=[('share', '=', False)],)
    
    def write(self, vals):
        member_ids = vals.get("member_ids")
        sale_spec_member_ids = vals.get("sale_spec_member_ids")
        if member_ids:
            if member_ids[0][2] != False:
                for user in member_ids[0][2]:
                    users_id = self.env['res.users'].search([('id', '=', user)])
                    if users_id:
                        if users_id.sale_team_id.id != self.id:
                            user_sale_team_history = self.env["users.sale.team.history"].create({
                                "user_id": users_id.id,
                                "team_id": self.id,
                                "team_id_date_time":datetime.now(),
                                "member_type":"user_id",})
        
        if sale_spec_member_ids:
            if sale_spec_member_ids[0][2] != False:
                for user in sale_spec_member_ids[0][2]:
                    users_id = self.env['res.users'].search([('id', '=', user)])
                    if users_id:
                        if users_id.sale_spec_team_id.id != self.id:
                            user_sale_team_history = self.env["users.sale.team.history"].create({
                                "user_id": users_id.id,
                                "team_id": self.id,
                                "team_id_date_time":datetime.now(),
                                "member_type":"sale_spec",})
    
        res = super(CrmTeam, self).write(vals)
        return res
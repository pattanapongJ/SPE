# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class WizardCreateSettlementsMall(models.TransientModel):
    _name = 'wizard.create.settlements.mall'
    _description = "Wizard to mark as done or create back order"

    generate_settle_commissions_mall_id = fields.Many2one('generate.settle.commissions.mall', string = 'Generate Settle Commissions Mall')
    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    user_id = fields.Many2one('res.users', string = 'Salesperson',)
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager")
    target_type_commission = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager_id', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager_id')

    target_type = fields.Selection([
        ('normal', 'Normal'),
        ('sold_out', 'Sold Out'),
    ], string="Commission Type",default='normal')

    create_type = fields.Selection([
        ('new_settlement', 'Create new settlements'),
        ('add_settlement', 'Add to settlements'),
    ], string="Create Type",default='new_settlement')
    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')

    @api.onchange('team_id','user_id','sale_spec','sale_manager_id','target_type','target_type_commission')
    def onchange_set_domain_settle_commissions_id(self):
        domain_settle_commissions_mall_id = [
            ('state', '=', 'draft'),
            ('team_id', '=', self.team_id.id),
            ('target_type', '=', self.target_type),
            ('target_type_commission', '=', self.target_type_commission)]
        if self.target_type_commission == 'user_id':
            domain_settle_commissions_mall_id += [('user_id', '=', self.user_id.id)]
        elif self.target_type_commission == 'sale_spec':
            domain_settle_commissions_mall_id += [('sale_spec', '=', self.user_id.id)]
        elif self.target_type_commission == 'sale_manager_id':
            domain_settle_commissions_mall_id += [('sale_manager_id', '=', self.user_id.id)]
        
        return {'domain': {'settle_commissions_mall_id':domain_settle_commissions_mall_id}}
    
    def action_make_settlement(self):
        if self.create_type == 'new_settlement':
            return self.generate_settle_commissions_mall_id.create_new_settlements()
        elif self.create_type == 'add_settlement':
            return self.generate_settle_commissions_mall_id.add_to_settlements(settle_commissions_mall_id=self.settle_commissions_mall_id.id)
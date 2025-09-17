# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class WizardCreateSettlements(models.TransientModel):
    _name = 'wizard.create.settlements'
    _description = "Wizard to mark as done or create back order"

    generate_settle_commissions_id = fields.Many2one('generate.settle.commissions', string = 'Generate Settle Commissions')
    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    user_id = fields.Many2one('res.users', string = 'Salesperson',)
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager")
    target_type = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager_id', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager_id')

    settle_type = fields.Selection([
        ('settle_payment', 'Commission by Payments'),
        ('settle_invoice', 'Commission by Invoices'),
    ], string="Settle Commission Type",default='settle_payment')
    create_type = fields.Selection([
        ('new_settlement', 'Create new settlements'),
        ('add_settlement', 'Add to settlements'),
    ], string="Create Type",default='new_settlement')
    settle_commissions_id = fields.Many2one('settle.commissions', string = 'Settle Commissions')

    @api.onchange('team_id','user_id','sale_spec','sale_manager_id','target_type','settle_type')
    def onchange_set_domain_settle_commissions_id(self):
        domain_settle_commissions_id = [
            ('state', '=', 'draft'),
            ('team_id', '=', self.team_id.id),
            ('settle_type', '=', self.settle_type),
            ('target_type', '=', self.target_type)]
        if self.target_type == 'user_id':
            domain_settle_commissions_id += [('user_id', '=', self.user_id.id)]
        elif self.target_type == 'sale_spec':
            domain_settle_commissions_id += [('sale_spec', '=', self.user_id.id)]
        elif self.target_type == 'sale_manager_id':
            domain_settle_commissions_id += [('sale_manager_id', '=', self.user_id.id)]
        
        return {'domain': {'settle_commissions_id':domain_settle_commissions_id}}
    
    def action_make_settlement(self):
        if self.create_type == 'new_settlement':
            return self.generate_settle_commissions_id.create_new_settlements()
        elif self.create_type == 'add_settlement':
            return self.generate_settle_commissions_id.add_to_settlements(settle_commissions_id=self.settle_commissions_id.id)
from odoo import models,fields,api,_

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    partner_group_id = fields.Many2one(comodel_name='partner.group', string='Partner Group', required=True, domain="['|', ('company_id', '=', current_company_id), ('company_id', '=', False)]")
    ref = fields.Char(string='Reference', index=True, copy=False)
    current_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Current Company',
        default=lambda self: self.env.company,
        store=False
    )
    
    @api.onchange('partner_group_id')
    def _oncahnge_patner_group(self):
        for account in self:
            account.property_account_receivable_id = account.partner_group_id.account_receivable_id
            account.property_account_payable_id = account.partner_group_id.account_payable_id
            account.property_account_position_id = account.partner_group_id.fiscal_position_id
    
    def _generate_seq_ref(self):
        for partner in self:
            partner_group = partner.partner_group_id
            res = partner_group.entry_sequence_id.next_by_id() or '/'
            return res
        
    @api.model   
    def create(self, vals):
        if not vals.get('ref') and 'ref' in vals and not self._context.get('from_copy') and vals.get('partner_group_id'):
            if vals.get('partner_group_id'):
                partner_group = self.env['partner.group'].browse(vals.get('partner_group_id'))
                if partner_group.entry_sequence_id:
                    vals['ref'] = partner_group.entry_sequence_id.next_by_id()
        return super(ResPartner, self).create(vals)
        
            
    def write(self, vals):
        if self._context.get('from_copy'):
            return super(ResPartner, self).write(vals)
        res = super(ResPartner, self).write(vals)
        
        if 'ref' in vals and not vals.get('ref'):
            partner_group = self.partner_group_id
            n_partner_group = self.partner_group_id
            if n_partner_group != partner_group or self.ref == False:
                if n_partner_group.entry_sequence_id:
                    self.ref = self._generate_seq_ref()
        return res
    
    def copy(self, default=None):
        self.ensure_one()
        chosen_name = default.get('name') if default else ''
        new_name = chosen_name or _('%s (copy)', self.name)
        default = dict(default or {}, name=new_name)
        default.update({'ref': '/'})
        return super(ResPartner, self.with_context(from_copy=True)).copy(default)
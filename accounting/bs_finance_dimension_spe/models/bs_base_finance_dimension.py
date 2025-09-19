from odoo import api, fields, models
from lxml import etree


class BSBaseFinanceDimension(models.AbstractModel):
    _inherit = 'bs.base.finance.dimension'

    finance_dimension_4_id = fields.Many2one('bs.finance.dimension', string="Dimension 4",
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_4').id)],ondelete='set null')
    finance_dimension_5_id = fields.Many2one('bs.finance.dimension', string='Dimension 5',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_5').id)],ondelete='set null')
    finance_dimension_6_id = fields.Many2one('bs.finance.dimension', string='Dimension 6',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_6').id)],ondelete='set null')
    finance_dimension_7_id = fields.Many2one('bs.finance.dimension', string='Dimension 7',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_7').id)],ondelete='set null')
    finance_dimension_8_id = fields.Many2one('bs.finance.dimension', string='Dimension 8',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_8').id)],ondelete='set null')
    finance_dimension_9_id = fields.Many2one('bs.finance.dimension', string='Dimension 9',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_9').id)],ondelete='set null')
    finance_dimension_10_id = fields.Many2one('bs.finance.dimension', string='Dimension 10',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension_spe.bs_dimension_10').id)],ondelete='set null')
    
    
    
    

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        _dimension4 = self.env.ref('bs_finance_dimension_spe.bs_dimension_4', raise_if_not_found=False)
        _dimension5 = self.env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
        _dimension6 = self.env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
        _dimension7 = self.env.ref('bs_finance_dimension_spe.bs_dimension_7', raise_if_not_found=False)
        _dimension8 = self.env.ref('bs_finance_dimension_spe.bs_dimension_8', raise_if_not_found=False)
        _dimension9 = self.env.ref('bs_finance_dimension_spe.bs_dimension_9', raise_if_not_found=False)
        _dimension10 = self.env.ref('bs_finance_dimension_spe.bs_dimension_10', raise_if_not_found=False)
        
        
        
        if res.get('finance_dimension_4_id') and _dimension4:
            res['finance_dimension_4_id']['string'] = _dimension4.name
        if res.get('finance_dimension_5_id') and _dimension5:
            res['finance_dimension_5_id']['string'] = _dimension5.name
        if res.get('finance_dimension_6_id') and _dimension6:
            res['finance_dimension_6_id']['string'] = _dimension6.name  
        if res.get('finance_dimension_7_id') and _dimension7:
            res['finance_dimension_7_id']['string'] = _dimension7.name
        if res.get('finance_dimension_8_id') and _dimension8:
            res['finance_dimension_8_id']['string'] = _dimension8.name
        if res.get('finance_dimension_9_id') and _dimension9:
            res['finance_dimension_9_id']['string'] = _dimension9.name
        if res.get('finance_dimension_10_id') and _dimension10:
            res['finance_dimension_10_id']['string'] = _dimension10.name
        return res

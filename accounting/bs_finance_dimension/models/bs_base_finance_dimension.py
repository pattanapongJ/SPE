from odoo import api, fields, models
from lxml import etree


class BSBaseFinanceDimension(models.AbstractModel):
    _name = 'bs.base.finance.dimension'

    finance_dimension_1_id = fields.Many2one('bs.finance.dimension', string="Dimension 1",
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension.bs_dimension_1').id)],ondelete='set null')
    finance_dimension_2_id = fields.Many2one('bs.finance.dimension', string='Dimension 2',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension.bs_dimension_2').id)],ondelete='set null')
    finance_dimension_3_id = fields.Many2one('bs.finance.dimension', string='Dimension 3',
                                             domain=lambda self: [('group_id', '=', self.env.ref(
                                                 'bs_finance_dimension.bs_dimension_3').id)],ondelete='set null')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
        _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
        _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
        if res.get('finance_dimension_1_id') and _dimension1:
            res['finance_dimension_1_id']['string'] = _dimension1.name
        if res.get('finance_dimension_2_id') and _dimension2:
            res['finance_dimension_2_id']['string'] = _dimension2.name
        if res.get('finance_dimension_3_id') and _dimension3:
            res['finance_dimension_3_id']['string'] = _dimension3.name
        return res

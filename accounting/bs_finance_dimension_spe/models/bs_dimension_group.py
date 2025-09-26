# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BsDimensionGroup(models.Model):
    _inherit = 'bs.dimension.group'

    ref_model = fields.Many2one(
        'ir.model',
        string="Reference Model",
        readonly=True
    )

    def create_finance_dimensions_initial_data(self):
        """Create bs.finance.dimension records for all datas based on this dimension group."""
        _dimension5 = self.env.ref('bs_finance_dimension_spe.bs_dimension_5', raise_if_not_found=False)
        _dimension6 = self.env.ref('bs_finance_dimension_spe.bs_dimension_6', raise_if_not_found=False)
        _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
        for group in self:
            if group.ref_model:
                _model_name = group.ref_model.model
                domain = []
                if group == _dimension5 and _model_name == 'res.partner':
                    domain = [('customer', '=', True)]
                elif group == _dimension6 and _model_name == 'res.partner':
                    domain = [('supplier', '=', True)]
                elif group == _dimension2 and _model_name == 'res.users':
                    domain = [('sale_team_id', '!=', False)]
                records = self.env[_model_name].search(domain)
                dimension_datas = []
                for data in records:
                    dimension_datas.append({
                        'name': data.display_name,
                        'group_id': group.id,
                        'res_id': data.id,
                        'company_id': self.env.company.id,
                    })
                    if data.id < 1:
                        raise ValidationError("Zero ID")
                if dimension_datas:
                    self.env['bs.finance.dimension'].create(dimension_datas)

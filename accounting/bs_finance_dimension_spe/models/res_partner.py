# -*- coding: utf-8 -*-
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_archive(self):
        """Archive the partner and update finance dimensions accordingly."""
        self._update_dimension_status(active=False)
        return super(ResPartner, self).action_archive()

    def action_unarchive(self):
        """Unarchive the partner and update finance dimensions accordingly."""
        self._update_dimension_status(active=True)
        return super(ResPartner, self).action_unarchive()

    @api.model
    def create(self, vals):
        """Create a new partner and initialize finance dimensions."""
        partner = super(ResPartner, self).create(vals)
        partner._manage_dimensions()
        return partner

    def write(self, vals):
        """Update partner details and adjust finance dimensions if needed."""
        res = super(ResPartner, self).write(vals)
        if 'name' in vals or 'firstname' in vals or 'lastname' in vals:
            self._update_dimension_name()
        if 'customer' in vals or 'supplier' in vals:
            self._manage_dimensions()
        return res

    def unlink(self):
        """Delete the partner and associated finance dimensions."""
        self._remove_all_dimensions()
        return super(ResPartner, self).unlink()

    def _manage_dimensions(self):
        """Create or delete dimensions based on partner type."""
        for partner in self:
            if partner.customer:
                partner._create_or_update_dimension('bs_finance_dimension_spe.bs_dimension_5')
            else:
                partner._remove_dimension('bs_finance_dimension_spe.bs_dimension_5')

            if partner.supplier:
                partner._create_or_update_dimension('bs_finance_dimension_spe.bs_dimension_6')
            else:
                partner._remove_dimension('bs_finance_dimension_spe.bs_dimension_6')

    def _update_dimension_status(self, active=True):
        """Archive or unarchive existing finance dimensions."""
        dimension_groups = self._get_dimension_groups()
        for group in dimension_groups:
            existing_dimensions = group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id in self.ids)
            if active:
                existing_dimensions.action_unarchive()
            else:
                existing_dimensions.action_archive()

    def _update_dimension_name(self):
        """Update the name of existing finance dimensions."""
        dimension_groups = self._get_dimension_groups()
        for partner in self:
            for group in dimension_groups:
                existing_dimension = group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id == partner.id)
                if existing_dimension:
                    existing_dimension.write({'name': partner.display_name})

    def _remove_all_dimensions(self):
        """Remove all finance dimensions associated with the partner."""
        dimension_groups = self._get_dimension_groups()
        for group in dimension_groups:
            existing_dimensions = group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id in self.ids)
            existing_dimensions.unlink()

    def _remove_dimension(self, dimension_group_xmlid):
        """Remove a specific finance dimension associated with the partner."""
        dimension_group = self.env.ref(dimension_group_xmlid)
        existing_dimension = dimension_group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id == self.id)
        if existing_dimension:
            existing_dimension.unlink()

    def _create_or_update_dimension(self, dimension_group_xmlid):
        """Create or update a finance dimension for the partner."""
        dimension_group = self.env.ref(dimension_group_xmlid)
        existing_dimension = dimension_group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id == self.id)
        if existing_dimension:
            existing_dimension.write({'name': self.display_name})
        else:
            self.env['bs.finance.dimension'].create({
                'name': self.display_name,
                'group_id': dimension_group.id,
                'res_id': self.id,
                'company_id': self.env.company.id,
            })

    def _get_dimension_groups(self):
        """Get all relevant dimension groups."""
        return [
            self.env.ref('bs_finance_dimension_spe.bs_dimension_5'),
            self.env.ref('bs_finance_dimension_spe.bs_dimension_6'),
        ]

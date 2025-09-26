# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_archive(self):
        """Archive the user and update finance dimensions accordingly."""
        self._update_finance_dimensions(active=False)
        return super(ResUsers, self).action_archive()

    def action_unarchive(self):
        """Unarchive the user and update finance dimensions accordingly."""
        self._update_finance_dimensions(active=True)
        return super(ResUsers, self).action_unarchive()

    @api.model
    def create(self, vals):
        """Create a new user and initialize finance dimensions."""
        user = super(ResUsers, self).create(vals)
        user._update_finance_dimensions()
        return user

    def write(self, vals):
        """Update user details and adjust finance dimensions if needed."""
        res = super(ResUsers, self).write(vals)
        if 'name' in vals:
            self._update_finance_dimensions()
        if 'sale_team_id' in vals:
            self._update_finance_dimensions(delete=not bool(self.sale_team_id))
        return res

    def unlink(self):
        """Delete the user and associated finance dimensions."""
        self._update_finance_dimensions(delete=True)
        return super(ResUsers, self).unlink()

    def _update_finance_dimensions(self, delete=False, active=None):
        """Manage the finance dimensions based on user state and type."""
        for user in self:
            user._manage_dimension(delete=delete, active=active)

    def _manage_dimension(self, delete=False, active=None):
        """Create, update, archive, or delete finance dimensions."""
        dimension_group = self._get_dimension_group()
        existing_dimension = dimension_group.with_context(active_test=False).finance_dimension_ids.filtered(
            lambda x: x.res_id == self.id)

        if existing_dimension:
            if delete:
                existing_dimension.unlink()
            elif active is not None:
                self._set_dimension_active_status(existing_dimension, active)
            else:
                existing_dimension.write({'name': self.display_name})
        elif not delete:
            self._create_dimension(dimension_group)

    def _get_dimension_group(self):
        """Determine the appropriate finance dimension group based on user type."""
        return self.env.ref('bs_finance_dimension.bs_dimension_2')

    def _set_dimension_active_status(self, dimension, active):
        """Set the active status of the finance dimension."""
        if active:
            dimension.action_unarchive()
        else:
            dimension.action_archive()

    def _create_dimension(self, dimension_group):
        """Create a new finance dimension for the user."""
        self.env['bs.finance.dimension'].create({
            'name': self.display_name,
            'group_id': dimension_group.id,
            'res_id': self.id,
            'company_id': self.company_id.id,
        })

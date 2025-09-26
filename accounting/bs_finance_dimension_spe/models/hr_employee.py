# -*- coding: utf-8 -*-
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = 'hr.employee'

    def action_archive(self):
        """Archive the employee and update finance dimensions accordingly."""
        self._update_finance_dimensions(active=False)
        return super(Employee, self).action_archive()

    def action_unarchive(self):
        """Unarchive the employee and update finance dimensions accordingly."""
        self._update_finance_dimensions(active=True)
        return super(Employee, self).action_unarchive()

    @api.model
    def create(self, vals):
        """Create a new employee and initialize finance dimensions."""
        employee = super(Employee, self).create(vals)
        employee._update_finance_dimensions()
        return employee

    def write(self, vals):
        """Update employee details and adjust finance dimensions if needed."""
        res = super(Employee, self).write(vals)
        if 'name' in vals:
            self._update_finance_dimensions()
        return res

    def unlink(self):
        """Delete the employee and associated finance dimensions."""
        self._update_finance_dimensions(delete=True)
        return super(Employee, self).unlink()

    def _update_finance_dimensions(self, delete=False, active=None):
        """Manage the finance dimensions based on employee state and type."""
        for employee in self:
            employee._manage_dimension(delete=delete, active=active)

    def _manage_dimension(self, delete=False, active=None):
        """Create, update, archive, or delete finance dimensions."""
        dimension_group = self._get_dimension_group()
        existing_dimension = dimension_group.with_context(active_test=False).finance_dimension_ids.filtered(lambda x: x.res_id == self.id)

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
        """Determine the appropriate finance dimension group based on employee type."""
        return self.env.ref('bs_finance_dimension_spe.bs_dimension_4')

    def _set_dimension_active_status(self, dimension, active):
        """Set the active status of the finance dimension."""
        if active:
            dimension.action_unarchive()
        else:
            dimension.action_archive()

    def _create_dimension(self, dimension_group):
        """Create a new finance dimension for the employee."""
        self.env['bs.finance.dimension'].create({
            'name': self.display_name,
            'group_id': dimension_group.id,
            'res_id': self.id,
            'company_id': self.company_id.id,
        })

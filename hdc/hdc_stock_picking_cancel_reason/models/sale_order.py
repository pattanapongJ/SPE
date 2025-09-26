# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add = [("waiting_cancel", "Waiting for cancel"), ("done",)], )
    status_cancel = fields.Boolean(string="Waiting for cancel",default=False )

    def action_cancel1(self):
        self.action_cancel_reason()

    def action_cancel(self):
        check_cancel = False
        for pick in self.picking_ids:
            if pick.state != "cancel":
                # pick.state_before_cancel = pick.state
                # pick.state = "waiting_cancel"
                check_cancel = True
        if check_cancel:
            self.state = "waiting_cancel"
            raise ValidationError(_("Please Cancel Delivery before."))

        res = super(SaleOrder, self).action_cancel()
        return res
        

    def action_cancel_reason(self):
        check_cancel = False
        for pick in self.picking_ids:
            if pick.state != "cancel":
                pick.state_before_cancel = pick.state
                pick.state = "waiting_cancel"
                check_cancel = True
        # if self.status_cancel is True:
        #     raise ValidationError(_("Please Cancel Delivery before."))
        if check_cancel:
            self.state = "waiting_cancel"
            # raise ValidationError(_("Please Cancel Delivery before."))
            # self.status_cancel = True
        else:
            return self.action_cancel()
            # res = super(SaleOrder, self).action_cancel()
            # self.state = "cancel"
            




from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta


class DistributionDeliveryNoteInherit(models.Model):
    _inherit = "distribition.delivery.note"
    _description = "Distribution Delivery Note Reports"

    create_date_print = fields.Datetime(
        string="Creation Date", default=fields.Datetime.now
    )

    def print(self):

        self.write({'create_date_print': fields.Datetime.now()})

        return self.env.ref("hdc_tms_general_report.tms_report_view").report_action(self)

    def get_sale_order(self, so_bill):
        sale_id = self.env["sale.order"].search([("name", "=", so_bill)])
        return sale_id.customer_po
    
    
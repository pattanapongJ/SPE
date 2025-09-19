# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
from datetime import datetime, timedelta, date
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"
            
class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    sale_uom_map_ids = fields.Many2many(related="product_id.sale_uom_map_ids")

    # @api.onchange("sale_uom_map_ids")
    # def _onchange_sale_uom_map_ids(self):
    #     domain_uom = [("id", "in", self.sale_uom_map_ids.ids)]
    #     return {"domain": {"product_uom": domain_uom}}
    
    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        result = super().product_id_change()
        if self.product_id:
            product_uom = self.product_id.uom_map_ids.filtered(lambda l: l.is_default_sale == True).mapped("uom_id")
            if product_uom:
                self.product_uom = product_uom[0]
            # =========================================
            # ไม่รู้ว่าทำไมต้องทับ onchange_product กับโค็ตนี้มันทำให้ 
            # product_id_change มันไม่ทำงาน เลยต้องเอาโค็ตนี้มาใส่เอง
            # ไม่รู้การ์ดครับ ว่าทำไมถึงทับ function ผมแก้ไขให้หน้างาน
            name = self.product_id.name
            if self.product_id.description_sale:
                name = self.product_id.description_sale
            self.name = name
            # =========================================
        domain_uom = [("id", "in", self.sale_uom_map_ids.ids)]
        if result and 'domain' in result:
            result['domain']['product_uom'] = domain_uom
        else:
            result = {"domain": {"product_uom": domain_uom}}
        return result
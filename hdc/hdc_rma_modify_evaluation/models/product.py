# -*- coding: utf-8 -*
import logging
from odoo import api, fields, models, _
from odoo.tools import populate
from datetime import date, datetime, timedelta
from lxml import etree, html
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.template"

    is_repair = fields.Boolean(string='Is Repair')
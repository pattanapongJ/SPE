# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import collections
import datetime
import hashlib
import pytz
import threading
import re

import requests
from collections import defaultdict
from lxml import etree
from random import randint
from werkzeug import urls

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError

class Partner(models.Model):
    _inherit = "res.partner"

    def _get_name(self):
        name = super(Partner, self)._get_name()
        name = '[%s] %s' %(self.ref, name) if self.ref else '%s' %(name)
        return name
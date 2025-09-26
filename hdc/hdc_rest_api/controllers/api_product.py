# -*- coding: utf-8 -*-
import babel.messages.pofile
import base64
import copy
from datetime import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile
import requests
import xlrd
from inspect import signature
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata
import hmac
import datetime

import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools,fields
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response, root
from odoo.exceptions import AccessError, UserError, AccessDenied, ValidationError
from odoo.models import check_method_name
from odoo.service import db, security
from . import global_api
_logger = logging.getLogger(__name__)

class APIProductMaster(http.Controller):

    @http.route('/api/v1/search_product_pos', cors = "*", type = 'json', auth = "user")
    def search_product_pos(self, args ,kwargs):
        data = args[0]
        field_get = data.get("field_get",False)
        limit = kwargs.get('limit', 1)
        offset = kwargs.get('offset', 0)
        order = kwargs.get('order')
        domain = [("branch_id", "=", data.get("branch_id")),("type","in",["product","consu"]),("active", "=", data.get("active",True))]
        if data.get("name"):
            domain += ['|',("name", "ilike", data.get("name")),("default_code", "ilike", data.get("name"))]
        product_ids = request.env['product.product'].search(domain, limit=limit, offset=offset, order = order)
        product_data = []
        for product_id in product_ids:
            product = request.env['product.product'].browse(product_id.id)
            data_product = product.read(field_get)
            domain = [
                ('product_id', '=', product.id),
                # ('location_id.usage', '=', 'internal') 
            ]
            if data.get("branch_id"):
                domain.append(('location_id.branch_id', '=',data.get("branch_id")))
            quants = request.env['stock.quant'].search(domain)
            onhand_qty = sum(quants.mapped('quantity'))
            data_product[0].update({"onhand":onhand_qty})
            product_data.append(data_product)

        return product_data

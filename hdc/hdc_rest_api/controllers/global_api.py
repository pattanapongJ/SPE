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


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied, ValidationError
from odoo.models import check_method_name
from odoo.service import db, security

_logger = logging.getLogger(__name__)


def GET_LOG(self, args):
    model = "mail.message"
    method = "search_read"
    message = self._call_kw(model, method, args, {})
    result = []
    for mes in message:
        detail = []
        new_value = ""
        log_data = request.env['mail.tracking.value'].sudo().search([("mail_message_id", "=", mes.get("id"))])
        if log_data:
            for log in log_data:
                if log.new_value_integer:
                    new_value = "%s -> %s"%(log.old_value_integer, log.new_value_integer)
                if log.new_value_float:
                    new_value = "%s -> %s"%(log.old_value_float, log.new_value_float)
                if log.new_value_monetary:
                    new_value = "%s -> %s"%(log.old_value_monetary, log.new_value_monetary)
                if log.new_value_char:
                    new_value = "%s -> %s"%(log.old_value_char, log.new_value_char)
                if log.new_value_text:
                    new_value = "%s -> %s"%(log.old_value_text ,log.new_value_text)
                if log.new_value_datetime:
                    new_value = "%s -> %s"%(log.old_value_datetime, log.new_value_datetime)
                track_data = {
                    "description": log.field_desc,
                    "new_value": new_value
                    }
                detail.append(track_data)
        elif mes.get("description"):
            track_data = {
                "description": mes.get("description"),
                "new_value": new_value
                }
            detail.append(track_data)
        tracking = {
            "author_id": mes.get("reply_to"),
            "create_date": mes.get("date"),
            "body": detail
            }
        result.append(tracking)
    return result

def GET_ATTACHED_FILE(args):
    attachment = request.env['ir.attachment'].search(args)
    result = []
    for att in attachment:
        result.append({
            "id": att.id,
            "name": att.name,
            "type": att.type,
            "mimetype": att.mimetype,
            "create_date": att.create_date,
            "write_date": att.write_date,
            "write_uid": (att.write_uid.id, att.write_uid.name),
            "datafile": att.datas,
            })
    return result
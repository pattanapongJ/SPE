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
from . import global_api

_logger = logging.getLogger(__name__)


class APIReceiptMaster(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)

    def button_validate(self, args):
        get_picking = request.env['stock.picking'].search([('id', '=', args)])
        data = get_picking.button_validate()
        if data != True:
            context = {
                'active_model': 'stock.picking', 'active_ids': [get_picking.ids], 'active_id': get_picking.id,
                }
            if get_picking:
                if data.get('name') == "Immediate Transfer?":
                    picking = request.env['stock.immediate.transfer'].with_context(context).create({
                        'pick_ids': data.get('context').get('default_pick_ids'),
                        'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': get_picking.id})]
                        })
                else:
                    picking = request.env['stock.backorder.confirmation'].with_context(context).create({
                        'pick_ids': data.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': [
                            (0, 0, {'to_backorder': True, 'picking_id': get_picking.id})]
                        })

                return {"id": picking.id, "picking_id": get_picking.id, "massage": data.get('name')}
        else:
            return True

    # ------------ รับสินค้า --------------------
    @http.route('/api/v1/get_receipt_list', cors = "*", type = 'json', auth = "user")
    def get_receipt_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = [("is_return", "=", False),("picking_type_code", "=", "incoming")]
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("location_dest_id"):
            args_search += [("location_dest_id", "=", args[0].get("location_dest_id"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        picking_id = request.env['stock.picking'].search(args_search, offset =offset, limit =limit, order =order)
        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                stock_move_line = []
                for move in line.move_line_ids:
                    if move.product_qty == 0:
                        stock_move_line.append({
                            "id": move.id,
                            "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty,
                            "lot_id": (move.lot_id.id, move.lot_id.name),
                            "lot_name": move.lot_name,
                            "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id,
                    "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "reserved_availability": line.reserved_availability,
                    "forecast_availability": line.forecast_availability,
                    "product_uom_qty": line.product_uom_qty,
                    "quantity_done": line.quantity_done,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id,
                "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "date_done": pick.date_done,
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "picking_type_id": (pick.picking_type_id.id, pick.picking_type_id.name),
                "backorder_id": (pick.backorder_id.id, pick.backorder_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/create_receipt', cors = "*", type = 'json', auth = "user")
    def create_receipt(self, args):
        receipt = request.env['stock.picking'].create(args)
        return (receipt.id, receipt.name)

    @http.route('/api/v1/update_receipt', cors = "*", type = 'json', auth = "user")
    def update_receipt(self, args):
        if args:
            for val in args:
                pick = request.env['stock.picking'].browse(val[0])
                move_lines = val[1].get("move_lines")
                del val[1]["move_lines"]
                if pick:
                    pick.write(val[1])
                if move_lines:
                    for move in move_lines:
                        if move[0]:
                            move_line_nosuggest_ids = move[1].get("move_line_nosuggest_ids")
                            if move_line_nosuggest_ids:
                                for line in move_line_nosuggest_ids:
                                    if line[1].get('product_uom_id'):
                                        product_id = request.env['product.product'].browse(line[1].get('product_id'))
                                        uom_id = request.env['uom.uom'].browse(line[1].get('product_uom_id'))
                                        if product_id.uom_id.category_id.id != uom_id.category_id.id:
                                            raise UserError(
                                                _('You cannot use a UOM that is different from the product category.'))
                                    if line[0]:
                                        stock_move_line = request.env['stock.move.line'].browse(line[0])
                                        stock_move_line.write(line[1])
                                    else:
                                        stock_move_line = request.env['stock.move.line'].create(line[1])
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].browse(move[0])
                            stock_move.write(move[1])
                        else:
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].create(move[1])
            return True

    @http.route('/api/v1/validate_receipts', cors = "*", type = 'json', auth = "user")
    def validate_receipts(self, args):
        return self.button_validate(args)

    # ------------ ส่งสินค้า --------------------
    @http.route('/api/v1/get_delivery_list', cors = "*", type = 'json', auth = "user")
    def get_delivery_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = [("is_return", "=", False),("picking_type_code", "=", "outgoing"),("picking_type_id.addition_operation_types", "=", False)]
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("location_id"):
            args_search += [("location_id", "=", args[0].get("location_id"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        picking_id = request.env['stock.picking'].search(args_search, offset =offset, limit =limit, order =order)
        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                stock_move_line = []
                for move in line.move_line_ids:
                    if 	move.package_level_id == False or move.picking_type_entire_packs == False:
                        stock_move_line.append({
                            "id": move.id,
                            "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty,
                            "lot_id": (move.lot_id.id, move.lot_id.name),
                            "lot_name": move.lot_name,
                            "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id,
                    "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "product_uom_qty": line.product_uom_qty,
                    "reserved_availability": line.reserved_availability,
                    "forecast_availability": line.forecast_availability,
                    "quantity_done": line.quantity_done,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id,
                "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "date_done": pick.date_done,
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "picking_type_id": (pick.picking_type_id.id, pick.picking_type_id.name),
                "backorder_id": (pick.backorder_id.id, pick.backorder_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/create_delivery', cors = "*", type = 'json', auth = "user")
    def create_delivery(self, args):
        receipt = request.env['stock.picking'].create(args)
        return (receipt.id, receipt.name)

    @http.route('/api/v1/update_delivery', cors = "*", type = 'json', auth = "user")
    def update_delivery(self, args):
        if args:
            for val in args:
                pick = request.env['stock.picking'].browse(val[0])
                move_lines = val[1].get("move_lines")
                del val[1]["move_lines"]
                if pick:
                    pick.write(val[1])
                if move_lines:
                    for move in move_lines:
                        if move[0]:
                            move_line_nosuggest_ids = move[1].get("move_line_nosuggest_ids")
                            if move_line_nosuggest_ids:
                                for line in move_line_nosuggest_ids:
                                    if line[1].get('product_uom_id'):
                                        product_id = request.env['product.product'].browse(line[1].get('product_id'))
                                        uom_id = request.env['uom.uom'].browse(line[1].get('product_uom_id'))
                                        if product_id.uom_id.category_id.id != uom_id.category_id.id:
                                            raise UserError(_('You cannot use a UOM that is different from the product category.'))
                                    if line[0]:
                                        stock_move_line = request.env['stock.move.line'].browse(line[0])
                                        stock_move_line.write(line[1])
                                    else:
                                        stock_move_line = request.env['stock.move.line'].create(line[1])
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].browse(move[0])
                            stock_move.write(move[1])
                        else:
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].create(move[1])
            return True

    @http.route('/api/v1/validate_deliverys', cors = "*", type = 'json', auth = "user")
    def validate_delivery(self, args):
        return self.button_validate(args)

    @http.route('/api/v1/get_transfer_list', cors = "*", type = 'json', auth = "user")
    def get_transfer_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []

        args_search = [("is_return", "=", False),("picking_type_code", "=", "internal")]
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                product_id = request.env['product.product'].search(['|',("name", "ilike", args[0].get("name")),("default_code", "ilike", args[0].get("name"))])
                if product_id:
                    stock_move_id = request.env['stock.move'].search(
                        [("product_id", "in", product_id.ids)])
                    if stock_move_id:
                        args_search += ['|', ("name", "ilike", args[0].get("name")), ("move_lines", "in", stock_move_id.ids)]
                else:
                    args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("location_id"):
            args_search += [("location_id", "=", args[0].get("location_id"))]
        if args[0].get("location_dest_id"):
            args_search += [("location_dest_id", "=", args[0].get("location_dest_id"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        picking_id = request.env['stock.picking'].search(args_search, offset = offset, limit = limit, order = order)
        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                stock_move_line = []
                for move in line.move_line_ids:
                    if move.package_level_id == False or move.picking_type_entire_packs == False:
                        if move.product_id == line.product_id:
                            stock_move_line.append({
                                "id": move.id,
                                "product_id": (move.product_id.id, move.product_id.name),
                                "tracking": move.product_id.tracking,
                                "location_id": (move.location_id.id, move.location_id.complete_name),
                                "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                                "product_uom_qty": move.product_uom_qty,
                                "lot_id": (move.lot_id.id, move.lot_id.name),
                                "lot_name": move.lot_name,
                                "qty_done": move.qty_done,
                                "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                                })
                stock_move.append({
                    "id": line.id,
                    "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "reserved_availability": line.reserved_availability,
                    "forecast_availability": line.forecast_availability,
                    "product_uom_qty": line.product_uom_qty,
                    "quantity_done": line.quantity_done,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id,
                "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "date_done": pick.date_done,
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "picking_type_id": (pick.picking_type_id.id, pick.picking_type_id.name),
                "backorder_id": (pick.backorder_id.id, pick.backorder_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/create_transfer', cors = "*", type = 'json', auth = "user")
    def create_transfer(self, args):
        transfer = request.env['stock.picking'].create(args)
        return (transfer.id, transfer.name)

    @http.route('/api/v1/validate_transfer', cors = "*", type = 'json', auth = "user")
    def validate_transfer(self, args):
        return self.button_validate(args)

    @http.route('/api/v1/update_transfer', cors = "*", type = 'json', auth = "user")
    def update_transfer(self, args):
        if args:
            for val in args:
                pick = request.env['stock.picking'].browse(val[0])
                move_lines = val[1].get("move_lines")
                del val[1]["move_lines"]
                if pick:
                    pick.write(val[1])
                if move_lines:
                    for move in move_lines:
                        if move[0]:
                            move_line_nosuggest_ids = move[1].get("move_line_nosuggest_ids")
                            if move_line_nosuggest_ids:
                                for line in move_line_nosuggest_ids:
                                    if line[1].get('product_uom_id'):
                                        product_id = request.env['product.product'].browse(line[1].get('product_id'))
                                        uom_id = request.env['uom.uom'].browse(line[1].get('product_uom_id'))
                                        if product_id.uom_id.category_id.id != uom_id.category_id.id:
                                            raise UserError(
                                                _('You cannot use a UOM that is different from the product category.'))
                                    if line[0]:
                                        stock_move_line = request.env['stock.move.line'].browse(line[0])
                                        stock_move_line.write(line[1])
                                    else:
                                        stock_move_line = request.env['stock.move.line'].create(line[1])
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].browse(move[0])
                            stock_move.write(move[1])
                        else:
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].create(move[1])
            return True

    @http.route('/api/v1/get_return_list', cors = "*", type = 'json', auth = "user")
    def get_return_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        stock_move_line = []
        args_search = [("is_return", "=", True)]
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("picking_type_code"):
            args_search += [("picking_type_code", "=", args[0].get("picking_type_code"))]
        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("location_id"):
            args_search += [("location_id", "=", args[0].get("location_id"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        picking_id = request.env['stock.picking'].search(args_search, offset = offset, limit = limit, order = order)
        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                for move in line.move_line_ids:
                    if move.package_level_id == False or move.picking_type_entire_packs == False:
                        stock_move_line.append({
                            "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty, "lot_id": (move.lot_id.id, move.lot_id.name),
                            "lot_name": move.lot_name, "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id, "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name), "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "reserved_availability": line.reserved_availability,
                    "forecast_availability": line.forecast_availability, "product_uom_qty": line.product_uom_qty,
                    "quantity_done": line.quantity_done,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id, "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "date_done": pick.date_done,
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "picking_type_id": (pick.picking_type_id.id, pick.picking_type_id.name),
                "picking_type_code": pick.picking_type_code,
                "backorder_id": (pick.backorder_id.id, pick.backorder_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/get_scrap_list', cors = "*", type = 'json', auth = "user")
    def get_scrap_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        multi_scrap_id = request.env['multi.stock.scrap'].search(args_search, offset = offset, limit = limit, order = order)
        for scrap in multi_scrap_id:
            scrap_lines = []
            for line in scrap.scrap_line:
                scrap_lines.append({
                    "id": line.id,
                    "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "tracking": line.product_id.tracking,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "lot_id": (line.lot_id.id, line.lot_id.name),
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "scrap_location_id": (line.scrap_location_id.id, line.scrap_location_id.complete_name),
                    "scrap_qty": line.scrap_qty,
                    "product_uom_id": (line.product_uom_id.id, line.product_uom_id.name)
                    })

            result.append({
                "id": scrap.id,
                "name": scrap.name,
                "scheduled_date": scrap.scheduled_date,
                "partner_id": (scrap.partner_id.id, scrap.partner_id.name),
                "origin": scrap.origin,
                "picking_id": (scrap.picking_id.id, scrap.picking_id.name),
                "location_id": (scrap.location_id.id, scrap.location_id.complete_name),
                "scrap_location_id": (scrap.scrap_location_id.id, scrap.scrap_location_id.complete_name),
                "user_id": (scrap.user_id.id, scrap.user_id.name),
                "state": scrap.state,
                "scrap_line": scrap_lines
                })
        return result

    @http.route('/api/v1/create_return', cors = "*", type = 'json', auth = "user")
    def create_return(self, args):
        scrap = request.env['multi.stock.scrap'].create(args)
        return (scrap.id, scrap.name)

    @http.route('/api/v1/update_return', cors = "*", type = 'json', auth = "user")
    def update_return(self, args):
        if args:
            for val in args:
                scrap_id = request.env['multi.stock.scrap'].browse(val[0])
                scrap_line = val[1].get("scrap_line")
                del val[1]["scrap_line"]
                if scrap_id:
                    scrap_id.write(val[1])
                if scrap_line:
                    for line in scrap_line:
                        if line[0]:
                            scrap = request.env['stock.scrap'].browse(line[0])
                            scrap.write(line[1])
                        else:
                            scrap = request.env['stock.scrap'].create(line[1])
            return True

    @http.route('/api/v1/get_stock_list', cors = "*", type = 'json', auth = "user")
    def get_stock_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        
        if args[0].get("id"):
            args_search += [("id", "=", args[0].get("id"))]
        if args[0].get("name"):
            args_search += [("name", "ilike", args[0].get("name"))]
        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        inventory_id = request.env['stock.inventory'].search(args_search, offset=offset, limit=limit, order=order)
        limit_line = args[0].get('limit_line')
        offset_line = args[0].get('offset_line')
        order_line = args[0].get('order_line')
        for stock in inventory_id:
            stock_lines = []
            stock_lines_ids = request.env['stock.inventory.line'].search([('inventory_id', '=', stock.id)], offset=offset_line, limit=limit_line, order=order_line)
            for line in stock_lines_ids:
                quant_id = request.env['stock.quant'].search([("product_id", "=", line.product_id.id), ("location_id", "=", line.location_id.id)],limit = 1)
                stock_lines.append({
                    "id": line.id,
                    "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "prod_lot_id": (line.prod_lot_id.id, line.prod_lot_id.name),
                    "package_id": (line.package_id.id or False, line.package_id.name or False),
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "stock_available": quant_id.available_quantity or 0,
                    "theoretical_qty": line.theoretical_qty,
                    "product_qty": line.product_qty,
                    "difference_qty": line.difference_qty,
                    "product_uom_id": (line.product_uom_id.id, line.product_uom_id.name)
                    })
            location_ids = []
            product_ids = []
            for location in stock.location_ids:
                location_ids.append((location.id, location.name))
            for product in stock.product_ids:
                product_ids.append((product.id, product.name))

            result.append({
                "id": stock.id,
                "name": stock.name,
                "accounting_date": stock.accounting_date,
                "user_id": (stock.user_id.id, stock.user_id.name),
                "approver_id": (stock.approver_id.id, stock.approver_id.name),
                "approver_date": stock.approver_date,
                "location_ids": location_ids,
                "product_ids": product_ids,
                "prefill_counted_quantity": stock.prefill_counted_quantity,
                "state": stock.state,
                "company_id": (stock.company_id.id, stock.company_id.name),
                "line_ids": stock_lines
                })
        return result

    @http.route('/api/v1/create_stock', cors = "*", type = 'json', auth = "user")
    def create_stock(self, args):
        stock = request.env['stock.inventory'].create(args)
        return (stock.id, stock.name)

    @http.route('/api/v1/update_stock', cors = "*", type = 'json', auth = "user")
    def update_stock(self, args):
        if not args:
            return {"error": "No data provided."}
        missing_lots = []
        mismatched_lots = []
        for val in args:
            stock = request.env['stock.inventory'].browse(val[0])
            move_lines = val[1].get("line_ids")
            del val[1]["line_ids"]
            if stock:
                stock.write(val[1])
            if move_lines:
                for move in move_lines:
                    if move[0]:
                        stock_line = request.env['stock.inventory.line'].browse(move[0])
                        if stock_line:
                            stock_line.write(move[1])
                    else:
                        # Check for inventory_id
                        if not move[1].get("inventory_id") and val[0]:
                            move[1]["inventory_id"] = val[0]
                        elif not move[1].get("inventory_id") and not val[0]:
                            return {"error": "inventory_id is missing, unable to create stock line."}

                        # Check for product_id
                        if not move[1].get("product_id"):
                            return {"error": "Missing product_id in stock line."}

                        product_id = move[1]["product_id"]

                        # Check for prod_lot and fetch lot_id
                        if move[1].get("prod_lot"):
                            lot_name = move[1]["prod_lot"]
                            lot = request.env['stock.production.lot'].search([('name', '=', lot_name)], limit=1)
                            if lot:
                                # Validate lot matches product_id
                                if lot.product_id.id != product_id:
                                    mismatched_lots.append({
                                        "prod_lot": lot_name,
                                        "expected_product_id": product_id,
                                        "actual_product_id": lot.product_id.id,
                                    })
                                    continue
                                move[1]["prod_lot_id"] = lot.id
                            else:
                                missing_lots.append(lot_name)
                                continue
                            # Remove prod_lot after processing
                            del move[1]["prod_lot"]

                        # Create stock inventory line
                        request.env['stock.inventory.line'].sudo().create(move[1])
        if missing_lots or mismatched_lots:
            return {
                "error": "Some issues were found with the provided data.",
                "missing_lots": missing_lots,
                "mismatched_lots": mismatched_lots,
            }
        return {"success": True}

    @http.route('/api/v1/get_borrow_list', cors = "*", type = 'json', auth = "user")
    def get_borrow_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        stock_move_line = []
        args_search = [("picking_type_code", "=", "outgoing"),
                       ("addition_operation_types.code", "=", "AO-02")]
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|', ("name", "ilike", args[0].get("name")), '|',
                                ("origin", "ilike", args[0].get("name")), ("partner_id", "in", partner_id.ids)]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")), ("origin", "ilike", args[0].get("name"))]

        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("location_id"):
            args_search += [("location_id", "=", args[0].get("location_id"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        picking_id = request.env['stock.picking'].search(args_search, offset = offset, limit = limit, order = order)
        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                for move in line.move_line_ids:
                    if move.package_level_id == False or move.picking_type_entire_packs == False:
                        stock_move_line.append({
                            "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty, "lot_id": (move.lot_id.id, move.lot_id.name),
                            "lot_name": move.lot_name, "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id, "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name), "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "reserved_availability": line.reserved_availability,
                    "forecast_availability": line.forecast_availability, "product_uom_qty": line.product_uom_qty,
                    "quantity_done": line.quantity_done,
                    "return_done": line.return_done,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id, "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "date_done": pick.date_done,
                "request_date": pick.request_date,
                "borrow_date": pick.borrow_date,
                "return_date": pick.return_date,
                "requestor_emp":  (pick.requestor_emp.id, pick.requestor_emp.name),
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "picking_type_id": (pick.picking_type_id.id, pick.picking_type_id.name),
                "picking_type_code": pick.picking_type_code,
                "backorder_id": (pick.backorder_id.id, pick.backorder_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/create_borrow', cors = "*", type = 'json', auth = "user")
    def create_borrow(self, args):
        receipt = request.env['stock.picking'].create(args)
        return (receipt.id, receipt.name)

    @http.route('/api/v1/update_borrow', cors = "*", type = 'json', auth = "user")
    def update_borrow(self, args):
        if args:
            for val in args:
                pick = request.env['stock.picking'].browse(val[0])
                move_lines = val[1].get("move_lines")
                del val[1]["move_lines"]
                if pick:
                    pick.write(val[1])
                if move_lines:
                    for move in move_lines:
                        if move[0]:
                            move_line_nosuggest_ids = move[1].get("move_line_nosuggest_ids")
                            if move_line_nosuggest_ids:
                                for line in move_line_nosuggest_ids:
                                    if line[1].get('product_uom_id'):
                                        product_id = request.env['product.product'].browse(line[1].get('product_id'))
                                        uom_id = request.env['uom.uom'].browse(line[1].get('product_uom_id'))
                                        if product_id.uom_id.category_id.id != uom_id.category_id.id:
                                            raise UserError(
                                                _('You cannot use a UOM that is different from the product category.'))
                                    if line[0]:
                                        stock_move_line = request.env['stock.move.line'].browse(line[0])
                                        stock_move_line.write(line[1])
                                    else:
                                        stock_move_line = request.env['stock.move.line'].create(line[1])
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].browse(move[0])
                            stock_move.write(move[1])
                        else:
                            if move[1].get("move_line_nosuggest_ids"):
                                del move[1]["move_line_nosuggest_ids"]
                            stock_move = request.env['stock.move'].create(move[1])
            return True


    @http.route('/api/v1/search_stock_quant', cors = "*", type = 'json', auth = "user")
    def search_stock_quant(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        if args[0].get("product"):
            args_search += [("display_name", "ilike", args[0].get("product"))]
        if args[0].get("location"):
            args_search += [("location_id", "in", args[0].get("location"))]
        if args[0].get("lot"):
            args_search += [("lot_id", "in", args[0].get("lot"))]

        quant_id = request.env['stock.quant'].search(args_search, offset = offset, limit = limit, order = order)
        quant_count = request.env['stock.quant'].search_count(args_search)
        for stock in quant_id:
            result.append({
                "id": stock.id,
                "image_128": stock.product_id.image_128,
                "product_id": stock.product_id.id,
                "product_name": stock.product_id.name,
                "product_code": stock.product_id.default_code,
                "lot_id": stock.lot_id.id,
                "lot_name": stock.lot_id.name,
                "location_id": stock.location_id.id,
                "location_name": stock.location_id.display_name,
                "price": stock.product_id.lst_price,
                "cost_price": stock.product_id.standard_price,
                "on_hand_qty": stock.inventory_quantity,
                "available_qty": stock.available_quantity,
                "product_uom_id": stock.product_uom_id.id,
                "product_uom_name": stock.product_uom_id.name,
                })
        return result

    @http.route('/api/v1/return_borrow',cors="*", type='json', auth="user")
    def GET_RETURN_RECEIPTS(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        product_return = []
        context = {
            'active_model': 'stock.picking',
            'active_ids': [picking.id],
            'active_id': picking.id,
        }
        return_picking = picking.env['stock.return.picking'].with_context(context).create({
                        'picking_id': picking.id
                    })
        return_picking._onchange_picking_id()
        if return_picking.product_return_moves:
            model_line = "stock.return.picking.line"
            method = "search_read"
            picking = ["id", "in", [return_picking.product_return_moves.id]]
            product_return = self._call_kw(model_line, method, [[picking],["product_id","lot_ids","quantity","uom_id"]], {})

        return {"id": return_picking.id, "moves_id": product_return}

    @http.route('/api/v1/update_return_borrow', type='json', auth="user")
    def UPDATE_RETURN_RECEIPTS(self, moves_id):
        for list in moves_id:
            model_line = "stock.return.picking.line"
            method_line = "write"
            move_line = self._call_kw(model_line, method_line, list, {})

        return moves_id

    @http.route('/api/v1/print_receipt',cors="*", type='json', auth="user")
    def print_receipt(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        report = request.env.ref('hdc_inventory_general_report.receipt_inventory_report_view')._render_qweb_pdf(picking.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/print_internal_tranfer',cors="*", type='json', auth="user")
    def internal_tranfer(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        report = request.env.ref('hdc_inventory_general_report.internal_tranfer_inventory_report_view')._render_qweb_pdf(picking.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/print_delivery',cors="*", type='json', auth="user")
    def print_delivery(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        report = request.env.ref('hdc_inventory_general_report.delivery_inventory_report_view')._render_qweb_pdf(picking.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/print_return',cors="*", type='json', auth="user")
    def print_return(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        report = request.env.ref('hdc_inventory_general_report.return_cus_inventory_report_view')._render_qweb_pdf(picking.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/print_count_sheet',cors="*", type='json', auth="user")
    def print_count_sheet(self, order_id):
        stock = request.env['stock.inventory'].browse(order_id)
        report = request.env.ref('stock.action_report_inventory')._render_qweb_pdf(stock.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/print_borrow',cors="*", type='json', auth="user")
    def print_borrow(self, order_id):
        picking = request.env['stock.picking'].browse(order_id)
        report = request.env.ref('hdc_inventory_general_report.requestion_inventory_report_view')._render_qweb_pdf(picking.ids)
        return base64.encodebytes(report[0]).decode('ascii')
    
    @http.route('/api/v1/create_picking', cors = "*", type = 'json', auth = "user")
    def create_picking(self, args):
        data = args[0]
        move_lines = []
        branch = request.env['res.branch'].search([('id','=',data.get('branch_id'))],limit = 1)
        for product in data.get("move_line"):
            product_id = request.env['product.product'].search([('id','=',product['product_id'])],limit = 1)
            if product_id :
                move_lines.append([0, 0, {
                    'product_id': product['product_id'],
                    'product_uom_qty': product['product_uom_qty'],
                    'product_uom': product_id.uom_id.id,
                    # 'price_unit': product['price_unit'],
                    'description_picking': product_id.display_name,
                    'name': product_id.display_name
                }])
        picking_vals = {
                'origin': data.get('origin', False),
                'partner_id': data.get('partner_id', False),
                'user_id': data.get('user_id', False),
                'scheduled_date': data.get('scheduled_date'),
                'picking_type_id': branch.picking_type_id.id,
                'company_id': data.get('company_id'),
                # 'move_type': 'direct',
                'note': data.get('note',False),
                'location_id': branch.location_id.id,
                'location_dest_id': branch.location_dest_id.id,
                'branch_id': data.get('branch_id'),
                'move_lines': move_lines,
            }
        picking = request.env['stock.picking'].create(picking_vals)
        result = []
        stock_move_line = []
        for pick in picking:
            stock_move = []
            for line in pick.move_lines:
                for move in line.move_line_ids:
                    if move.package_level_id == False or move.picking_type_entire_packs == False:
                        stock_move_line.append({
                            "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty, "lot_id": (move.lot_id.id, move.lot_id.name),
                            "lot_name": move.lot_name, "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id, "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name), 
                    "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "quantity_done": line.quantity_done,
                    "product_uom_qty": line.product_uom_qty,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })
            result.append({
                "id": pick.id, 
                "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "branch_id": (pick.branch_id.id, pick.branch_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                })
        return (result)
        # return (picking.id, picking.name)
    
    @http.route('/api/v1/get_picking_list', cors = "*", type = 'json', auth = "user")
    def get_picking_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        if args[0].get("name"):
            args_search += [("name", "ilike", args[0].get("name"))]
        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("date_from"):
            args_search += [("scheduled_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("scheduled_date", "<=", args[0].get("date_to"))]
        if args[0].get("branch_id"):
            args_search += [("branch_id", "=", args[0].get("branch_id"))]
        if args[0].get("picking_type_id"):
            args_search += [("picking_type_id", "=", args[0].get("picking_type_id"))]
        if args[0].get("is_requisition") :
            picking_type_id = request.env['stock.picking.type'].search([("is_requisition", "=", True)],limit=1)
            if picking_type_id :
                args_search += [("picking_type_id", "=", picking_type_id.id)]

        picking_id = request.env['stock.picking'].search(args_search, offset = offset, limit = limit, order = order)
        if args[0].get("picking_id"):
            picking_id = request.env['stock.picking'].search([("id", "=", args[0].get("picking_id"))], limit = 1)

        for pick in picking_id:
            stock_move = []
            for line in pick.move_lines:
                stock_move_line = []
                for move in line.move_line_ids:
                    if move.package_level_id == False or move.picking_type_entire_packs == False:
                        stock_move_line.append({
                            "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                            "tracking": move.product_id.tracking,
                            "location_id": (move.location_id.id, move.location_id.complete_name),
                            "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                            "product_uom_qty": move.product_uom_qty, 
                            "lot_id": (move.lot_id.id, move.lot_id.name),
                            "package_id": (move.package_id.id or False, move.package_id.name or False),
                            "result_package_id": (move.result_package_id.id or False, move.result_package_id.name or False),
                            "lot_name": move.lot_name, "qty_done": move.qty_done,
                            "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                            })
                stock_move.append({
                    "id": line.id, "image_128": line.product_id.image_128,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name), 
                    "tracking": line.product_id.tracking,
                    "location_id": (line.location_id.id, line.location_id.complete_name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "quantity_done": line.quantity_done,
                    "product_uom_qty": line.product_uom_qty,
                    "product_uom": (line.product_uom.id, line.product_uom.name),
                    "move_line_nosuggest_ids": stock_move_line
                    })

            args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": pick.id, 
                "name": pick.name,
                "scheduled_date": pick.scheduled_date,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "origin": pick.origin,
                "location_id": (pick.location_id.id, pick.location_id.complete_name),
                "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "branch_id": (pick.branch_id.id, pick.branch_id.name),
                "state": pick.state,
                "note": pick.note,
                "move_lines": stock_move,
                })
        return result
    
    @http.route('/api/v1/check_product_available_in_branch', cors = "*", type = 'json', auth = "user")
    def check_product_available_in_branch(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        qty = args[0].get("qty")
        result = []
        picking_center = False
        if args[0].get("default_code") and args[0].get("product_name") and args[0].get("qty") and args[0].get("uom") and args[0].get("branch_name"):
            product_ids = request.env['product.product'].search([("default_code", "=", args[0].get("default_code")), ("name", "=", args[0].get("product_name"))])
            # have product
            if product_ids:
                product_id = False
                uom_id = False
                for prod in product_ids:
                    uom_id = request.env['uom.uom'].search([("name", "=", args[0].get("uom"))], limit=1)
                    if not uom_id:
                        return [{"status": "false", "message": "Unit not found in product."}]
                    product_id = prod
                    if prod.uom_id.id != uom_id.id:
                        try:
                            qty = prod.uom_id._compute_quantity(qty, uom_id)
                        except:
                            return [{"status": "false", "message":  f"Cannot convert UOM '{uom_id.name}' to '{product_id.uom_id.name}'."}]
                    else:
                        uom_id = product_id.uom_id
                get_branch = request.env['res.branch'].search([("name", "=", args[0].get("branch_name"))], limit=1)
                if get_branch:
                    branch_id = get_branch[0].id
                    warehouse_id = request.env['stock.warehouse'].search([("branch_id", "=", branch_id)])
                    location_id = request.env['stock.location'].search([("branch_id", "=", branch_id)])
                    # not found warehouse
                    if not warehouse_id:
                        return [{"status": "false", "message": "Not found warehouse in branch."}]
                    elif len(warehouse_id) > 1:
                        return [{"status": "false", "message": "There cannot be more than 1 warehouse in a branch."}]
                    # have location
                    if location_id:
                        args_search = [("product_id", "=", product_id.id),("location_id", "in", location_id.ids),("product_uom_id", "=", product_id.uom_id.id)]
                        quant_ids = request.env['stock.quant'].search(args_search, offset = offset, limit = limit, order = order)
                        if quant_ids:
                            available_qty = 0
                            available_center_qty = 0
                            is_available = False
                            for stock in quant_ids:
                                available_qty += stock.available_quantity
                            if not available_qty >= qty:
                                location_center_id = False
                                params = request.env['ir.config_parameter'].sudo()
                                operation_type_setting_id = int(params.get_param('hdc_resupply.operation_type_setting_id'))
                                if operation_type_setting_id:
                                    picking_type = request.env["stock.picking.type"].search([('id',"=", operation_type_setting_id)], limit=1)
                                    if picking_type:
                                        picking_center = picking_type[0]
                                        branch_center_id = picking_center.default_location_src_id.branch_id
                                        if branch_center_id:
                                            if operation_type_setting_id:
                                                location_center_id = request.env["stock.location"].search([("branch_id", "=", branch_center_id.id)])
                                            if location_center_id:
                                                args_search = [("product_id", "=", product_id.id),("location_id", "=", location_center_id.id),("product_uom_id", "=", product_id.uom_id.id)]
                                                quant_location_ids = request.env['stock.quant'].search(args_search, offset = offset, limit = limit, order = order)
                                                if quant_location_ids:
                                                    for stock_center in quant_location_ids:
                                                        available_center_qty += stock_center.available_quantity
                            if available_qty + available_center_qty >= qty:
                                is_available = True
                                return [{
                                    "status": "true", 
                                    "default_code": args[0].get("default_code"),
                                    "demand_qty": args[0].get("qty"),
                                    "available_qty": available_qty,
                                    "is_available": is_available
                                    }]  
                            else:
                                # Create external center to branch
                                orderpoint_ids = request.env['stock.warehouse.orderpoint'].search([('product_id','=',product_id.id), ("warehouse_id", "=", warehouse_id.id), ("product_uom", "=", product_id.uom_id.id)])
                                if not orderpoint_ids:
                                    return [{"status": "false", "message": "Not found recording rule."}]
                                else:
                                    orderpoint_id = orderpoint_ids.filtered(lambda lm: lm.location_id == warehouse_id.lot_stock_id)
                                    if not orderpoint_id:
                                        return [{"status": "false", "message": "Not found recording rule. (location = %s)" % warehouse_id.lot_stock_id.display_name}]
                                    else:
                                        picking = request.env['stock.picking'].create({
                                            "picking_type_id": picking_center.id,
                                            "location_id": picking_center.default_location_src_id.id,
                                            "location_dest_id": warehouse_id.lot_stock_id.id,
                                            "branch_id": branch_id,
                                            "move_lines": [(0, 0, {
                                                "product_id": product_id.id,
                                                "name": product_id.name,
                                                "product_uom_qty": orderpoint_id[0].product_max_qty,
                                                "product_uom": product_id.uom_id.id,
                                                "location_id": picking_center.default_location_src_id.id,
                                                "location_dest_id": warehouse_id.lot_stock_id.id,
                                                })]
                                            })
                                        return [{
                                            "status": "true", 
                                            "picking_id": picking.id,
                                            "default_code": args[0].get("default_code"),
                                            "demand_qty": args[0].get("qty"),
                                            "available_qty": available_qty,
                                            "is_available": is_available,
                                            }]  
                        return [{"status": "false", "message": "Not found movement."}]                
                    return [{"status": "false", "message": "Not found location in branch."}]
                return [{"status": "false", "message": "No branch found in the system"}]                 
            return [{"status": "false", "message": "Can’t found product on odoo."}] 
        return result


    @http.route('/api/v1/check_delivery_area', cors = "*", type = 'json', auth = "user")
    def check_delivery_area(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        if args[0].get("search_name"):
            city_id = request.env['res.city.zip'].search([("display_name", "ilike", args[0].get("search_name"))])
            delivery_id = request.env['resupply.location.tab'].search([("zip_id", "in", city_id.ids)],
                                                                                  offset = offset, limit = limit, order = order)
        else:
            return result

        for delivery in delivery_id:
            address = delivery.zip_id.city_id.name.split(", ")
            result.append({
                    "id": delivery.location_line_id.id,
                    "branch_name": delivery.location_line_id.branch_id.name,
                    "sub_district": address[0],
                    "district": address[1],
                    "province": delivery.zip_id.city_id.state_id.name,
                    "province_id": delivery.zip_id.city_id.state_id.id,
                    "zip": delivery.zip_id.name,
                    "country": delivery.zip_id.city_id.country_id.name,
                    "country_id": delivery.zip_id.city_id.country_id.id,
                    "location": delivery.zip_id.display_name
                })
        return result
    
    @http.route('/api/v1/put_detail_operation', cors="*", type='json', auth="user")
    def put_detail_operation(self, args, kwargs):
        data = args[0]
        if not data or not isinstance(data, dict):
            return {
                'status': 'error',
                'message': 'Invalid input data format'
            }

        move_lines = data.get("move_line", [])

        picking_id = data.get("picking_id")
        if not picking_id:
            return {
                'status': 'error',
                'message': 'Picking ID is required'
            }

        order_lines = []
        errors = []

        Picking = request.env['stock.picking']

        stock_picking = Picking.browse(picking_id)
        if not stock_picking.exists():
            raise UserError("Stock Picking not found")
        try:
            for move_line in move_lines:
                product_id = move_line.get('product_id')
                location_id = move_line.get('location_id')
                qty_done = move_line.get('qty_done')
                
                if not product_id or not location_id or qty_done is None:
                    errors.append(f"Invalid move line data: {move_line}")
                    continue

                move_id = request.env['stock.move'].search([
                    ('product_id', '=', product_id),
                    ('picking_id', '=', picking_id)
                ], limit=1)
                if not move_id :
                    errors.append(f"Picking Not found Product ID: {product_id}")
                    continue
                product_uom_id = move_id.product_uom.id
                
                line_data = {
                    'picking_id': picking_id,
                    'product_id': product_id,
                    'location_id': location_id,
                    'qty_done': qty_done,
                    'product_uom_id': product_uom_id,
                    'move_id': move_id.id,
                }
                
                if 'location_dest_id' in move_line:
                    line_data['location_dest_id'] = move_line['location_dest_id']
                if 'lot_id' in move_line:
                    line_data['lot_id'] = move_line['lot_id']
                if 'lot_name' in move_line:
                    line_data['lot_name'] = move_line['lot_name']
                if 'package_id' in move_line:
                    line_data['package_id'] = move_line['package_id']

                order_lines.append(line_data)

            request.env['stock.move.line'].create(order_lines)

        except UserError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f'Unexpected error: {str(e)}')
        stock_move_details = []
        for move in stock_picking.move_ids_without_package:
            move_line_nosuggest = []
            for line in move.move_line_nosuggest_ids:
                line_data = {
                    'id': line.id,
                    'product_id': [line.product_id.id, line.product_id.name],
                    'tracking': move.product_id.tracking,
                    'location_id': [line.location_id.id, line.location_id.name],
                    'location_dest_id': [line.location_dest_id.id, line.location_dest_id.name],
                    'product_uom_qty': line.product_uom_qty,
                    'lot_id': [line.lot_id.id if line.lot_id else False, line.lot_id.name if line.lot_id else False],
                    'package_id': [line.package_id.id if line.package_id else False, line.package_id.name if line.package_id else False],
                    'lot_name': line.lot_name if line.lot_name else False,
                    'qty_done': line.qty_done,
                    'product_uom_id': [line.product_uom_id.id, line.product_uom_id.name]
                }
                move_line_nosuggest.append(line_data)
            stock_move_details.append({
                'id': move.id,
                'product_id': move.product_id.id,
                'product_uom_qty': move.product_uom_qty,
                'quantity_done': move.quantity_done,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'name': move.name,
                'move_line_nosuggest': move_line_nosuggest
            })
        if errors:
            return {
                'status': 'error',
                'errors': errors
            }

        return {
            'status': 'success',
            'picking_id': picking_id,
            'stock_move': stock_move_details
        }
    
    @http.route('/api/v1/update_lot', cors="*", type='json', auth="user")
    def update_lot(self, args, kwargs):
        try:
            # Access models
            data = args[0]
            Picking = request.env['stock.picking']
            StockMoveLine = request.env['stock.move.line']
            picking_id = data.get('picking_id')
            move_lines = data.get('move_line', [])
            
            # Validate picking
            stock_picking = Picking.browse(picking_id)
            if not stock_picking.exists():
                raise UserError("Stock Picking not found")
            
            if not move_lines:
                raise UserError("move_lines is required")
            
            created_move_lines = []
            for line in move_lines:
                line_id = line.get('line_id')
                qty_done = line.get('qty_done')

                # Validate required fields
                if not line_id or not qty_done:
                    raise UserError("line_id and qty_done are required for each move line")
                
                move_line = StockMoveLine.browse(line_id)
                if not move_line.exists():
                    raise UserError(f"Move Line with id {line_id} not found")

                # Update qty_done and lot
                vals = {
                    'qty_done': qty_done,
                }
                
                move_line.write(vals)
            stock_picking = Picking.browse(picking_id)

            result = []
            stock_move_line = []
            for pick in stock_picking:
                stock_move = []
                for line in pick.move_lines:
                    for move in line.move_line_ids:
                        if move.package_level_id == False or move.picking_type_entire_packs == False:
                            stock_move_line.append({
                                "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                                "tracking": move.product_id.tracking,
                                "location_id": (move.location_id.id, move.location_id.complete_name),
                                "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                                "product_uom_qty": move.product_uom_qty, "lot_id": (move.lot_id.id, move.lot_id.name),
                                "lot_name": move.lot_name, "qty_done": move.qty_done,
                                "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                                })
                    stock_move.append({
                        "id": line.id, "image_128": line.product_id.image_128,
                        "default_code": line.product_id.default_code,
                        "product_id": (line.product_id.id, line.product_id.name), 
                        "tracking": line.product_id.tracking,
                        "location_id": (line.location_id.id, line.location_id.complete_name),
                        "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                        "quantity_done": line.quantity_done,
                        "product_uom_qty": line.product_uom_qty,
                        "product_uom": (line.product_uom.id, line.product_uom.name),
                        "move_line_nosuggest_ids": stock_move_line
                        })

                args_attached = [("res_model", "=", "stock.picking"), ("res_id", "=", pick.id)]

                result.append({
                    "id": pick.id, 
                    "name": pick.name,
                    "scheduled_date": pick.scheduled_date,
                    "partner_id": (pick.partner_id.id, pick.partner_id.name),
                    "origin": pick.origin,
                    "location_id": (pick.location_id.id, pick.location_id.complete_name),
                    "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                    "user_id": (pick.user_id.id, pick.user_id.name),
                    "branch_id": (pick.branch_id.id, pick.branch_id.name),
                    "state": pick.state,
                    "note": pick.note,
                    "move_lines": stock_move,
                    })

            # Return updated picking data
            return {
                'status': 'success',
                'result': result,
                # 'move_lines': result,
            }
        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'An unexpected error occurred: ' + str(e)
            }
    @http.route('/api/v1/put_detail_operation_line', cors="*", type='json', auth="user")
    def put_detail_operation_line(self, args, kwargs):
        try:
            data = args[0]
            move_id = data.get('move_id')
            move_lines = data.get('move_line', [])
            
            if not move_id:
                raise UserError("move_id is required")

            StockMove = request.env['stock.move']
            StockMoveLine = request.env['stock.move.line']
            ProductProduct = request.env['product.product']

            stock_move = StockMove.browse(move_id)
            if not stock_move.exists():
                raise UserError("Stock Move not found")

            created_move_lines = []

            for line in move_lines:
                product_id = line.get('product_id')
                location_id = line.get('location_id')
                location_dest_id = line.get('location_dest_id')
                qty_done = line.get('qty_done')
                lot_id = line.get('lot_id')
                lot_name = line.get('lot_name')
                package_id = line.get('package_id')

                if not product_id or not location_id or not location_dest_id or not qty_done:
                    raise UserError("product_id, location_id, location_dest_id, and qty_done are required for each move line")

                product_uom_id = stock_move.product_uom.id
                vals = {
                    'move_id': stock_move.id,
                    'product_id': product_id,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'product_uom_id': product_uom_id,
                    'qty_done': qty_done,
                }
                if lot_id:
                    vals['lot_id'] = lot_id
                if lot_name:
                    vals['lot_name'] = lot_name #ใบรับที่เป็นlot/serialต้องใส่
                if package_id:
                    vals['package_id'] = package_id

                move_line = StockMoveLine.create(vals)
                created_move_lines.append(move_line.id)

            # ดึงข้อมูล stock move
            stock_move_data = stock_move.read([
                'id', 'location_id', 'location_dest_id', 'reserved_availability',
                'forecast_availability', 'product_uom_qty', 'quantity_done', 'product_uom'
            ])[0]

            # ดึงข้อมูลจาก product
            product = ProductProduct.browse(stock_move.product_id.id)
            product_data = product.read(['image_128', 'default_code', 'tracking'])[0]
            stock_move_data.update({
                'image_128': product_data['image_128'],
                'default_code': product_data['default_code'],
                'product_id': [product.id, product.name],
                'tracking': product_data['tracking']
            })

            # ดึงข้อมูล move_line_nosuggest_ids
            move_lines = StockMoveLine.search([('move_id', '=', stock_move.id),('product_qty', '=', 0),('qty_done', '!=', 0)])
            stock_move_data['move_line_nosuggest_ids'] = []
            for line in move_lines:
                product = ProductProduct.browse(line.product_id.id)
                line_data = {
                    'id': line.id,
                    'product_id': [line.product_id.id, line.product_id.name],
                    'tracking': product.tracking,
                    'location_id': [line.location_id.id, line.location_id.name],
                    'location_dest_id': [line.location_dest_id.id, line.location_dest_id.name],
                    'product_uom_qty': line.product_uom_qty,
                    'lot_id': [line.lot_id.id if line.lot_id else False, line.lot_id.name if line.lot_id else False],
                    'package_id': [line.package_id.id if line.package_id else False, line.package_id.name if line.package_id else False],
                    'lot_name': line.lot_name,
                    'qty_done': line.qty_done,
                    'product_uom_id': [line.product_uom_id.id, line.product_uom_id.name]
                }
                stock_move_data['move_line_nosuggest_ids'].append(line_data)
            picking = stock_move.picking_id
            return {
                'status': 'success',
                'picking_id': picking.id,
                'stock_move': stock_move_data
            }
        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': 'An unexpected error occurred: ' + str(e)
            }

    @http.route('/api/v1/get_package_list', cors = "*", type = 'json', auth = "user")
    def get_package_list(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        if args[0].get("package_id"):
            package_id = request.env['stock.quant.package'].search([("id", "=", args[0].get("picking_id"))], limit = 1)
        else:
            if args[0].get("name"):
                args_search += [("name", "ilike", args[0].get("name"))]
            package_id = request.env['stock.quant.package'].search(args_search, offset = offset, limit = limit, order = order)

        for pack in package_id:
            quant_ids = []
            if args[0].get("lot"):
                for line in pack.quant_ids.filtered(lambda r: r.lot_id.name == args[0].get("lot")):
                    quant_ids.append({
                        "id": line.id,
                        "product_id": (line.product_id.id, line.product_id.name),
                        "lot_id": (line.lot_id.id, line.lot_id.name),
                        "quantity": line.quantity,
                        "product_uom": (line.product_uom_id.id, line.product_uom_id.name),
                        })
                    result.append({
                        "id": pack.id, "name": pack.name, "quant_ids": quant_ids,
                        })
            else:
                for line in pack.quant_ids:
                    quant_ids.append({
                        "id": line.id,
                        "product_id": (line.product_id.id, line.product_id.name),
                        "lot_id": (line.lot_id.id, line.lot_id.name),
                        "quantity": line.quantity,
                        "product_uom": (line.product_uom_id.id, line.product_uom_id.name),
                        })

                    result.append({
                        "id": pack.id,
                        "name": pack.name,
                        "quant_ids": quant_ids,
                        })
        return result    
    
    @http.route('/api/v1/create_return_receive', cors = "*", type = 'json', auth = "user")
    def create_return_receive(self, args):
        data = args[0]
        move_lines = []
        errors = []
        branch = request.env['res.branch'].search([('id','=',data.get('branch_id'))],limit = 1)
        try:
            for product in data.get("move_line"):
                product_id = request.env['product.product'].search([('id','=',product['product_id'])],limit = 1)
                if product_id :
                    move_lines.append([0, 0, {
                        'product_id': product['product_id'],
                        'product_uom_qty': product['product_uom_qty'],
                        'product_uom': product_id.uom_id.id,
                        'description_picking': product_id.display_name,
                        'name': product_id.display_name
                    }])
            picking_vals = {
                    'origin': data.get('origin', False),
                    'partner_id': data.get('partner_id', False),
                    'user_id': data.get('user_id', False),
                    'scheduled_date': data.get('scheduled_date'),
                    'picking_type_id': branch.picking_type_return_id.id,
                    'company_id': data.get('company_id'),
                    'note': data.get('note',False),
                    'location_id': branch.picking_type_return_id.default_location_src_id.id,
                    'location_dest_id': branch.location_dest_id.id,
                    'branch_id': data.get('branch_id'),
                    'move_lines': move_lines,
                }
            picking = request.env['stock.picking'].create(picking_vals)
            result = []
            stock_move_line = []
            for pick in picking:
                pick.action_confirm()
                for product in data.get("move_line"):
                    for move_line in pick.move_ids_without_package.filtered(lambda ml: ml.product_id.id == product['product_id']):
                        # Check if the product is tracked by lot or serial
                        if move_line.product_id.tracking != 'none':
                            # Loop through lots for the current product
                            for lot in product.get('lots', []):
                                lot_id = request.env['stock.production.lot'].search([("name","=",lot['lot'])],limit=1)
                                # Find the move_line that matches the lot (or create one if necessary)
                                if lot_id:
                                    package_id = False
                                    if lot.get('package'):
                                        package_id = request.env['stock.quant.package'].search([
                                            ('name', '=', lot['package'])
                                        ], limit=1)
                                    move_line_new = request.env['stock.move.line'].create({
                                        'picking_id': picking.id,
                                        'move_id': move_line.id,
                                        'product_id': move_line.product_id.id,
                                        'location_id': branch.picking_type_return_id.default_location_src_id.id,
                                        'location_dest_id': move_line.location_dest_id.id,
                                        'lot_id': lot_id.id,  # Set the lot ID
                                        'qty_done': lot['qty'],  # Set the done quantity
                                        'product_uom_id': move_line.product_id.uom_id.id,
                                        'result_package_id': package_id.id if package_id else False,  # Set the package 
                                    })
                        else:
                            # For products with no tracking, simply update qty_done
                            move_line_new = request.env['stock.move.line'].create({
                                'picking_id': picking.id,
                                'move_id': move_line.id,
                                'product_id': move_line.product_id.id,
                                'location_id': branch.picking_type_return_id.default_location_src_id.id,
                                'location_dest_id': move_line.location_dest_id.id,
                                'qty_done': lot['qty'],  # Set the done quantity
                                'product_uom_id': move_line.product_uom_id.id,
                            })
                # Validate the delivery
                validate = pick.button_validate()
                if validate != True:
                    # Check if the validate result is asking for "Immediate Transfer"
                    context = {
                        'active_model': 'stock.picking', 'active_ids': [pick.ids], 'active_id': pick.id,
                        }
                    if validate.get('name') == "Immediate Transfer?":
                        immediate_transfer_wizard = request.env['stock.immediate.transfer'].with_context(context).create({
                            'pick_ids': validate.get('context').get('default_pick_ids'),
                            'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': pick.id})]
                            })
                        immediate = immediate_transfer_wizard.with_context(button_validate_picking_ids=pick.id).process()
                        # After Immediate Transfer, check if it asks to create a Backorder
                        if immediate != True:
                            if immediate.get('name') == "Create Backorder?":
                                backorder_wizard = request.env['stock.backorder.confirmation'].with_context(context).create({
                                    'pick_ids': validate.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': [
                                        (0, 0, {'to_backorder': True, 'picking_id': pick.id})]
                                    })
                                # Cancel Backorder
                                backorder = backorder_wizard.with_context(button_validate_picking_ids=pick.id).process_cancel_backorder()

                    # Handle "Create Backorder" directly if it is not an immediate transfer
                    elif validate.get('name') == "Create Backorder?":
                        backorder_wizard = request.env['stock.backorder.confirmation'].with_context(context).create({
                            'pick_ids': validate.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': [
                                (0, 0, {'to_backorder': True, 'picking_id': pick.id})]
                            })
                        # Cancel Backorder
                        backordere = backorder_wizard.with_context(button_validate_picking_ids=pick.id).process_cancel_backorder()
                stock_move = []
                for line in pick.move_lines:
                    for move in line.move_line_ids:
                        if move.package_level_id == False or move.picking_type_entire_packs == False:
                            stock_move_line.append({
                                "id": move.id, "product_id": (move.product_id.id, move.product_id.name),
                                "tracking": move.product_id.tracking,
                                "location_id": (move.location_id.id, move.location_id.complete_name),
                                "location_dest_id": (move.location_dest_id.id, move.location_dest_id.complete_name),
                                "product_uom_qty": move.product_uom_qty, 
                                "lot_id": (move.lot_id.id, move.lot_id.name),
                                "package_id": [move.package_id.id if move.package_id else False, move.package_id.name if move.package_id else False],
                                "result_package_id": [move.result_package_id.id if move.result_package_id else False, move.result_package_id.name if move.package_id else False],
                                "lot_name": move.lot_name,
                                "qty_done": move.qty_done,
                                "product_uom_id": (move.product_uom_id.id, move.product_uom_id.name)
                                })
                    stock_move.append({
                        "id": line.id, "image_128": line.product_id.image_128,
                        "default_code": line.product_id.default_code,
                        "product_id": (line.product_id.id, line.product_id.name), 
                        "tracking": line.product_id.tracking,
                        "location_id": (line.location_id.id, line.location_id.complete_name),
                        "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                        "quantity_done": line.quantity_done,
                        "product_uom_qty": line.product_uom_qty,
                        "product_uom": (line.product_uom.id, line.product_uom.name),
                        "move_line_nosuggest_ids": stock_move_line
                        })
                result.append({
                    "id": pick.id,
                    "name": pick.name,
                    "scheduled_date": pick.scheduled_date,
                    "partner_id": (pick.partner_id.id, pick.partner_id.name),
                    "origin": pick.origin,
                    "location_id": (pick.location_id.id, pick.location_id.complete_name),
                    "location_dest_id": (pick.location_dest_id.id, pick.location_dest_id.complete_name),
                    "user_id": (pick.user_id.id, pick.user_id.name),
                    "branch_id": (pick.branch_id.id, pick.branch_id.name),
                    "state": pick.state,
                    "note": pick.note,
                    "move_lines": stock_move,
                    })
        except Exception as e:
            errors.append('Unexpected error: {}'.format(str(e)))
        if errors:
            return {'status': 'error', 'message': ' '.join(errors)}
        return (result)
        # return (picking.id, picking.name)

    @http.route('/api/v1/print_label_lot', cors="*", type='json', auth="user")
    def print_label_lot(self, args, **kwargs):
        try:
            # Extract the lot IDs from the request
            lots = args[0].get("lot_ids")
            if not lots:
                return {"error": "No lot_ids provided"}
            
            # Search for the stock.production.lot records
            lot_ids = request.env['stock.production.lot'].search([("id", "in", lots)])
            if not lot_ids:
                return {"error": "No lots found for the given IDs"}

            # Report name
            report_name = 'hdc_product_gen_lot.report_quant_lot_barcode'

            # Use the `ir.actions.report` model to generate the report
            report = request.env['ir.actions.report']._get_report_from_name(report_name)
            if not report:
                return {"error": "Report not found"}

            pdf_content, content_type = report._render_qweb_pdf(lot_ids.ids)

            # Return the report as base64 encoded PDF
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

            return {
                'pdf_base64': pdf_base64,
                'content_type': content_type,
                'filename': 'lot_barcode_report.pdf'
            }
        
        except Exception as e:
            # Capture any exception and return a meaningful error message
            return {
                'error': 'An error occurred while generating the report',
                'details': str(e)
            }
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

def _rotate_session(httprequest):
    if httprequest.session.rotate:
        root.session_store.delete(httprequest.session)
        httprequest.session.sid = root.session_store.generate_key()
        if httprequest.session.uid:
            httprequest.session.session_token = security.compute_session_token(
                httprequest.session, request.env
            )
        httprequest.session.modified = True

class Session(http.Controller):

    @http.route('/web/session/authenticate', cors="*", type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        result = request.env["ir.http"].session_info()
        # avoid to rotate the session outside of the scope of this method
        # to ensure that the session ID does not change after this method
        _rotate_session(request)
        request.session.rotate = False
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days = 90)
        result["session"] = {
            "sid": request.session.sid, "expires_at": fields.Datetime.to_string(expiration),
            }
        return result

class Database(http.Controller):
    @http.route('/web/database/list', cors="*", type='json', auth='none')
    def list(self):
        """
        Used by Mobile application for listing database
        :return: List of databases
        :rtype: list
        """
        return http.db_list()

class APISaleMaster(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)
    
    def register_payment(self, args):
        data = args[0]
        invoice_id = data.get('invoice_id')

        payment_date = data.get('payment_date', fields.Date.today())
        invoice = request.env['account.move'].search([('id', '=', invoice_id), ('move_type', '=', 'out_invoice')], limit=1)
        if not invoice:
            return {'status': 'error', 'message': 'Invoice not found'}
        from_sale = data.get('from_sale')
        is_cash = data.get('is_cash')
        is_bank = data.get('is_bank')
        amount = data.get('amount')
        journal_id = data.get('journal_id')
        if from_sale:
            if not is_cash and not is_bank:
                return {'status': 'skip', 'message': 'Skip Register'}
            if is_cash:
                # cash_journal = request.env['ir.config_parameter'].sudo().set_param('hdc_addon_branch_api.default_cash_journal_id', False)
                cash_journal = invoice.branch_id.cash_journal_id.id
                if not cash_journal:
                    return {'status': 'error', 'message': 'please Setting Cash Journal!'}
                journal_id = cash_journal
            if is_bank:
                journal_id = invoice.branch_id.bank_journal_id.id
        if not data.get('amount'):
            amount = invoice.amount_total
        try:
            # Create a payment
            payment_register = request.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                'journal_id': journal_id,
                'amount': amount,
                'payment_date': payment_date,
                # 'payment_method_id': request.env.ref('account.account_payment_method_manual_in').id,
                'communication': invoice.name,
            })
            # Process the payment
            res = payment_register.action_create_payments()

        except UserError as e:
            return {'status': 'error', 'message': str(e)}

        return {
            'status': 'success',
            'message': 'Payment registered successfully',
            'invoice_id': invoice.id,
            'amount': amount,
            'payment_date': payment_date
        }
    

    @http.route('/api/v1/groups', cors="*", type='json', auth="user")
    def CHECK_GROUPS(self, full_name, users, path=None):
        user_res = request.env['res.groups'].sudo().search([("full_name" , "=" , full_name), ("users" , "=" , users)])
        if user_res:
            return True
        else:
            return False

    @http.route('/api/v1/download_sale_order', cors="*", type='json', auth="user")
    def download_sale_order(self, order_id):
        sale_order = request.env['sale.order'].browse(order_id)
        report = request.env.ref('sale.action_report_saleorder')._render_qweb_pdf(sale_order.ids)
        return base64.encodebytes(report[0]).decode('ascii')

    @http.route('/api/v1/get_sale_order', cors = "*", type = 'json', auth = "user")
    def get_sale_order(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        args_search = []
        if args[0].get("name"):
            partner_id = request.env['res.partner'].search([("name", "ilike", args[0].get("name"))])
            if partner_id:
                args_search += ['|',("name", "ilike", args[0].get("name")),
                                    '|',("origin", "ilike", args[0].get("name")),
                                    ("partner_id", "in", partner_id.ids)
                                ]
            else:
                args_search += ['|', ("name", "ilike", args[0].get("name")),
                                        ("origin", "ilike", args[0].get("name"))
                                   ]
        if args[0].get("state"):
            args_search += [("state", "=", args[0].get("state"))]
        if args[0].get("delivery_state"):
            args_search += [("delivery_state", "=", args[0].get("delivery_state"))]
        if args[0].get("date_from"):
            args_search += [("create_date", ">=", args[0].get("date_from"))]
        if args[0].get("date_to"):
            args_search += [("create_date", "<=", args[0].get("date_to"))]

        sale_order = request.env['sale.order'].search(args_search, offset = offset, limit = limit, order = order)
        for sale in sale_order:
            try:
                delivery_state = sale.delivery_state
            except:
                delivery_state = False
            try:
                payment_method_id = (sale.payment_method_id.id, sale.payment_method_id.name)
            except:
                payment_method_id = False

            order_line = []
            for line in sale.order_line:
                order_line.append({
                    "id": line.id, "image_128": line.product_id.image_128, "default_code": line.product_id.default_code,
                    "name": (line.product_id.id, line.product_id.name), "price_unit": line.price_unit,
                    "product_uom_qty": line.product_uom_qty,
                    "product_uom": (line.product_uom.id, line.product_uom.name), "amount_untaxed": line.price_subtotal,
                    "amount_tax": line.price_tax, "amount_total": line.price_total,
                    })
            args_log = [[["model", "=", "sale.order"], ["res_id", "=", sale.id]],
                        ["id", "description", "reply_to", "date"]]
            so_log = global_api.GET_LOG(self, args_log)

            args_attached = [("res_model", "=", "sale.order"), ("res_id", "=", sale.id)]
            so_attached = global_api.GET_ATTACHED_FILE(args_attached)

            result.append({
                "id": sale.id,
                "name": sale.name,
                "origin": sale.origin,
                "date_order": sale.date_order,
                "amount_undiscounted": sale.amount_undiscounted,
                "discount": sale.amount_undiscounted - sale.amount_untaxed,
                "amount_untaxed": sale.amount_untaxed,
                "amount_tax": sale.amount_tax,
                "amount_total": sale.amount_total,
                "state": sale.state,
                "delivery_state": delivery_state,
                "payment_method_id": payment_method_id,
                "partner_customer_id": (sale.partner_id.id, sale.partner_id.name),
                "partner_customer_firstname": sale.partner_id.firstname,
                "partner_customer_lastname": sale.partner_id.lastname,
                "partner_customer_name_company": sale.partner_id.name_company,
                "partner_customer_company_type": sale.partner_id.company_type,
                "customer_street": sale.partner_id.street, "customer_sub_district": sale.partner_id.sub_district,
                "customer_city": sale.partner_id.city,
                "customer_state_id": (sale.partner_id.state_id.id, sale.partner_id.state_id.name),
                "customer_zip": sale.partner_id.zip, "customer_mobile": sale.partner_id.mobile,
                "partner_invoice_id": (sale.partner_invoice_id.id, sale.partner_invoice_id.name),
                "partner_invoice_firstname": sale.partner_invoice_id.firstname,
                "partner_invoice_lastname": sale.partner_invoice_id.lastname,
                "partner_invoice_name_company": sale.partner_invoice_id.name_company,
                "partner_invoice_company_type": sale.partner_invoice_id.company_type,
                "invoice_street": sale.partner_invoice_id.street,
                "invoice_sub_district": sale.partner_invoice_id.sub_district,
                "invoice_city": sale.partner_invoice_id.city,
                "invoice_state_id": (sale.partner_invoice_id.state_id.id, sale.partner_invoice_id.state_id.name),
                "invoice_zip": sale.partner_invoice_id.zip, "invoice_mobile": sale.partner_invoice_id.mobile,
                "order_line": order_line, "message_log": so_log, "attachement": so_attached
                })
        return result


    @http.route('/api/v1/get_address', cors = "*", type = 'json', auth = "user")
    def get_address(self, args, kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        order = kwargs.get('order')
        result = []
        if args[0].get("name"):
            city_id = request.env['res.city.zip'].search([("display_name", "ilike", args[0].get("name"))], offset=offset, limit=limit, order=order)
        else:
            city_id = request.env['res.city.zip'].search([],offset = offset, limit = limit, order = order)

        for city in city_id:
            address = city.city_id.name.split(", ")
            result.append({
                "id": city.id,
                "name": city.display_name,
                "sub_district": address[0],
                "city": address[1],
                "province": city.city_id.state_id.name,
                "state_id": city.city_id.state_id.id,
                "zip": city.name,
                "country": city.city_id.country_id.name,
                "country_id": city.city_id.country_id.id,
                })
        return result

    @http.route('/api/v1/search_customer', cors = "*", type = 'json', auth = "user")
    def search_customer(self, args, kwargs):
        if not args[0].get("name") and not args[0].get("state_id") and not args[0].get("city") and not args[0].get("sub_district"):
            partner_id = self._call_kw("res.partner", "search_read", [[]], kwargs)
        else:
            state_id = args[0].get("state_id")
            if state_id:
                partner_id = self._call_kw("res.partner", "search_read", [['|', ("name", "ilike", args[0].get("name")),
                     ("mobile", "ilike", args[0].get("name")),
                     ("state_id", "in", state_id),
                     ("city", "ilike", args[0].get("city")),
                     ("sub_district", "ilike", args[0].get("sub_district"))]], kwargs)
            else:
                partner_id = self._call_kw("res.partner", "search_read",
                                           [['|', ["name", "ilike", args[0].get("name")],
                                            ["mobile", "ilike", args[0].get("name")],
                                            ["city", "ilike", args[0].get("city")],
                                            ["sub_district", "ilike", args[0].get("sub_district")]]], kwargs)
        return partner_id
    
    @http.route('/api/v1/search_customer_pos', cors="*", type='json', auth="user")
    def search_customer_pos(self, args, kwargs):
        data = args[0]
        name = data.get('name')
        vat = data.get('vat')
        phone = data.get('phone')
        limit = kwargs.get('limit', 10)
        offset = kwargs.get('offset', 0)
        order = kwargs.get('order')

        domain = []
        if phone:
            domain.append(('phone', '=', phone))
        if vat:
            domain.append(('vat', 'ilike', vat))
        if name:
            domain.append(('name', 'ilike', name))
        partners = request.env['res.partner'].search(domain, limit=limit, offset=offset, order = order)
        partner_data = []
        for partner_id in partners:
            partner = request.env['res.partner'].browse(partner_id.id)
            partner_data.append(partner.read())

        return partner_data
    
    @http.route('/api/v1/create_sale_order', cors="*", type='json', auth="user")
    def create_sale_order(self, args):
        data = args[0]
        order_lines = []
        errors = []

        opportunity_id = False
        origin = False
        if data.get('crm_id'):
            opportunity = request.env["crm.lead"].search([("id", "=", data.get('crm_id'))],limit=1)
            if opportunity :
                opportunity_id = opportunity.id
                origin = opportunity.code
                set_won = opportunity.action_set_won_rainbowman()
        
        for product in data.get("order_line"):
            product_id = request.env["product.product"].search([("id", "=", int(product['product_id']))],limit=1)
            if product_id:
                order_lines.append([0, 0, {
                    'product_id': product['product_id'],
                    'product_uom_qty': product['product_uom_qty'],
                    'product_uom': product_id.uom_id.id,
                    'price_unit': product['price_unit'],
                    'name': product_id.display_name
                }])
        if data.get("discount"):
            product_discount_id = request.env['ir.config_parameter'].sudo().get_param('hdc_rest_api.product_discount_id')
            discount_id = request.env["product.product"].search([("id", "=", int(product_discount_id))],limit=1)
            if discount_id:
                order_lines.append([0, 0, {
                    'product_id': discount_id.id,
                    'product_uom_qty': 1,
                    'product_uom': discount_id.uom_id.id,
                    'price_unit': data.get("discount"),
                    'name': discount_id.name
                }])
        if data.get("delivery_fee"):
            product_delivery_id = request.env['ir.config_parameter'].sudo().get_param('hdc_rest_api.product_delivery_id')
            delivery_id = request.env["product.product"].search([("id", "=", int(product_delivery_id))],limit=1)
            if delivery_id:
                order_lines.append([0, 0, {
                    'product_id': delivery_id.id,
                    'product_uom_qty': 1,
                    'product_uom': delivery_id.uom_id.id,
                    'price_unit': data.get("delivery_fee"),
                    'name': delivery_id.name
                }])

        prepare_date_sale = {
            "partner_id": data.get("partner_id"),
            "date_order": data.get("date_order"),
            "opportunity_id": opportunity_id,
            "origin": origin,
            "order_line": order_lines,
        }
        try:
            sale_order = request.env['sale.order'].create(prepare_date_sale)
            sale_order.action_confirm()
        except UserError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append('Unexpected error: {}'.format(str(e)))

        if errors:
            return {'status': 'error', 'message': ' '.join(errors)}
        
        # Confirm and Validate Delivery (Pickings)
        try:
            for picking in sale_order.picking_ids:
                if picking.state not in ['done', 'cancel']:
                    # Confirm and assign products for delivery
                    picking.action_confirm()
                    # Validate each move line (quantity done) รอเขียนหยอด move line no suggest
                    for product in data.get("order_line"):
                        for move_line in picking.move_ids_without_package.filtered(lambda ml: ml.product_id.id == product['product_id']):
                            # Check if the product is tracked by lot or serial
                            if move_line.product_id.tracking != 'none':
                                # Loop through lots for the current product
                                for lot in product.get('lots', []):
                                    lot_id = request.env['stock.production.lot'].search([("name","=",lot['lot'])],limit=1)
                                    # Find the move_line that matches the lot (or create one if necessary)
                                    package_id = False
                                    if lot.get('package'):
                                        package_id = request.env['stock.quant.package'].search([
                                            ('name', '=', lot['package'])
                                        ], limit=1)
                                    if lot_id:
                                        move_line_new = request.env['stock.move.line'].create({
                                            'picking_id': picking.id,
                                            'move_id': move_line.id,
                                            'product_id': move_line.product_id.id,
                                            'location_id': move_line.location_id.id,
                                            'location_dest_id': move_line.location_dest_id.id,
                                            'lot_id': lot_id.id,  # Set the lot ID
                                            'qty_done': lot['qty'],  # Set the done quantity
                                            'product_uom_id': move_line.product_id.uom_id.id,
                                            'package_id': package_id.id if package_id else False,  # Set the package 
                                        })
                            else:
                                # For products with no tracking, simply update qty_done
                                move_line_new = request.env['stock.move.line'].create({
                                    'picking_id': picking.id,
                                    'move_id': move_line.id,
                                    'product_id': move_line.product_id.id,
                                    'location_id': move_line.location_id.id,
                                    'location_dest_id': move_line.location_dest_id.id,
                                    'qty_done': lot['qty'],  # Set the done quantity
                                    'product_uom_id': move_line.product_uom_id.id,
                                })
                    
                    # Validate the delivery
                    validate = picking.button_validate()
                    if validate != True:
                        # Check if the validate result is asking for "Immediate Transfer"
                        context = {
                            'active_model': 'stock.picking', 'active_ids': [picking.ids], 'active_id': picking.id,
                            }
                        if validate.get('name') == "Immediate Transfer?":
                            immediate_transfer_wizard = request.env['stock.immediate.transfer'].with_context(context).create({
                                'pick_ids': validate.get('context').get('default_pick_ids'),
                                'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': picking.id})]
                                })
                            immediate = immediate_transfer_wizard.with_context(button_validate_picking_ids=picking.id).process()
                            # After Immediate Transfer, check if it asks to create a Backorder
                            if immediate != True:
                                if immediate.get('name') == "Create Backorder?":
                                    backorder_wizard = request.env['stock.backorder.confirmation'].with_context(context).create({
                                        'pick_ids': validate.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': [
                                            (0, 0, {'to_backorder': True, 'picking_id': picking.id})]
                                        })
                                    # Cancel Backorder
                                    backorder = backorder_wizard.with_context(button_validate_picking_ids=picking.id).process_cancel_backorder()

                        # Handle "Create Backorder" directly if it is not an immediate transfer
                        elif validate.get('name') == "Create Backorder?":
                            backorder_wizard = request.env['stock.backorder.confirmation'].with_context(context).create({
                                'pick_ids': validate.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': [
                                    (0, 0, {'to_backorder': True, 'picking_id': picking.id})]
                                })
                            # Cancel Backorder
                            backordere = backorder_wizard.with_context(button_validate_picking_ids=picking.id).process_cancel_backorder()
                            
        except UserError as e:
            pass
            # errors.append("Delivery error: {}".format(str(e)))
        except Exception as e:
            errors.append("Unexpected delivery error: {}".format(str(e)))
        if errors:
            return {'status': 'error', 'message': ' '.join(errors)}
        
        try:
            # Create the invoice
            invoice = sale_order._create_invoices()
            invoice.action_post()
        except UserError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append('Unexpected error: {}'.format(str(e)))

        if errors:
            return {'status': 'error', 'message': ' '.join(errors)}
        try:
            # register payment
            is_cash = data.get('is_cash')
            is_bank = data.get('is_bank')
            register_payment_args=[{'invoice_id': invoice.id, 
                                    # 'payment_date': fields.Date.today(), 
                                    # 'journal_id': 1,
                                    'is_cash': is_cash,'is_bank': is_bank,'from_sale': True, }]

            register_payment = self.register_payment(register_payment_args)
        except UserError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append('Unexpected error: {}'.format(str(e)))

        if errors:
            return {'status': 'error', 'message': ' '.join(errors)}
        
        return {
            'status': 'success',
            'sale_order_id': sale_order.id,
            'sale_order_name': sale_order.name,
            'invoice_id': invoice.id,
            'invoice_name': invoice.name
        }
    
    @http.route('/api/v1/register_payment_invoice', cors="*", type='json', auth="user")
    def register_payment_invoice(self, args):
        return self.register_payment(args)

    
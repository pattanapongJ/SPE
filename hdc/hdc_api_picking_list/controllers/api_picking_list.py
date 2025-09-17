# -*- coding: utf-8 -*-
import babel.messages.pofile
import base64
from datetime import datetime
from inspect import signature
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi


import odoo
import odoo.modules.registry
from odoo.api import call_kw
from odoo.tools.translate import _
from odoo import http, tools
from odoo.http import  request, serialize_exception as _serialize_exception, Response
from odoo.models import check_method_name
from odoo.exceptions import UserError, ValidationError
from . import global_api

class APIPickingListMaster(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)
    
    def button_validate_picking(self, args):
        get_picking = request.env['picking.lists'].search([('id', '=', args)])
        data = get_picking.action_validate()
        if data != None:
            if get_picking:
                if data.get('name') == "Create Backorder?":
                    picking = request.env['wizard.picking.list.backorder'].create({
                        'picking_lists': get_picking.id
                        })
                return {"id": picking.id, "picking_id": get_picking.id, "massage": data.get('name')}
        else:
            return True
    
    @http.route('/api/v1/confirm_nobackorder_pickinglist', cors="*", type='json', auth="user")
    def confirm_nobackorder_pickinglist(self, **kwargs):
        args = kwargs.get("args", [])
        if not args or not args[0]:
            return {"error": "Missing required parameter: picking list ID."}

        pickinglist = request.env['wizard.picking.list.backorder'].search([("id", "=", args[0])])
        if not pickinglist:
            return {"error": "Picking list not found with the given ID."}

        try:
            pickinglist.action_close()
            return {
                "success": True,
                "message": "Picking list confirmed without backorder.",
                "picking_id": pickinglist.picking_lists.id,
            }
        except ValidationError as e:
            return {
                "error": "Validation error occurred.",
                "message": str(e),
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred.",
                "message": str(e),
            }
        
    @http.route('/api/v1/confirm_backorder_pickinglist', cors="*", type='json', auth="user")
    def confirm_backorder_pickinglist(self, **kwargs):
        args = kwargs.get("args", [])
        if not args or not args[0]:
            return {"error": "Missing required parameter: picking list ID."}

        pickinglist = request.env['wizard.picking.list.backorder'].search([("id", "=", args[0])])
        if not pickinglist:
            return {"error": "Picking list not found with the given ID."}

        try:
            backorder = pickinglist.action_backorder()
            picking_lists = request.env['picking.lists'].search([('origin', '=', pickinglist.picking_lists.name)])
            return {
                "success": True,
                "message": "Picking list backorder created successfully.",
                "backorder_ids": picking_lists.ids,
            }
        except ValidationError as e:
            return {
                "error": "Validation error occurred.",
                "message": str(e),
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred.",
                "message": str(e),
            }


    @http.route('/api/v1/validate_picking', cors = "*", type = 'json', auth = "user")
    def validate_picking(self, args):
        return self.button_validate_picking(args)
    
    @http.route('/api/v1/cancel_picking', cors = "*", type = 'json', auth = "user")
    def cancel_picking(self, args):
        if not args or not args[0]:
            return {"error": "Missing required parameter: picking list ID."}

        picking_id = args[0][0] if isinstance(args[0], list) else args[0]
        picking = request.env['picking.lists'].search([("id", "=", picking_id)])
        if not picking:
            return {"error": "Picking list not found with the given ID."}

        try:
            picking_cancel = picking.action_cancel()
            return {
                "success": True,
                "message": "Picking list Cancel successfully.",
                "picking_id": picking.ids,
            }
        except ValidationError as e:
            return {
                "error": "Validation error occurred.",
                "message": str(e),
            }
        except UserError as e:
            # Handle user-specific errors gracefully
            return {
                "error": "UserError error occurred.",
                "message": str(e),
                "picking_id": picking_id
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred.",
                "message": str(e),
                "picking_id": picking_id,
            }
    
    @http.route('/api/v1/confirm_picking', cors="*", type='json', auth="user")
    def confirm_picking(self, **kwargs):
        # Extract `args` from `kwargs`
        args = kwargs.get("args", [])
        
        # Validate that args[0] is provided
        if not args or len(args) < 1 or not args[0]:
            return {"error": "Missing required parameter: picking ID."}

        # Search for the picking record
        picking_id = args[0][0] if isinstance(args[0], list) else args[0]
        picking = request.env['picking.lists'].search([("id", "=", picking_id)])
        
        if not picking:
            return {"error": "Picking not found with the given ID."}
        if picking.state != 'draft':
            return {
                "error": "Picking is not in the 'draft' state.",
                "current_state": picking.state,
            }
        
        try:
            # Call action_confirm and handle any validation errors
            picking.action_confirm()
            return {
                "success": True,
                "message": "Picking confirmed successfully.",
                "picking_id": picking_id,
            }
        except ValidationError as e:
            # Return a detailed validation error message
            return {
                "error": "Validation error occurred.",
                "message": str(e),
                "picking_id": picking_id
            }
        except UserError as e:
            # Handle user-specific errors gracefully
            return {
                "error": "UserError error occurred.",
                "message": str(e),
                "picking_id": picking_id
            }
        except Exception as e:
            # Catch unexpected exceptions for debugging
            return {
                "error": True,
                "message": "An unexpected error occurred.",
                "picking_id": picking_id
            }

    @http.route('/api/v1/checkavailable_picking', cors="*", type='json', auth="user")
    def checkavailable_picking(self, **kwargs):
        # Extract `args` from `kwargs`
        args = kwargs.get("args", [])
        
        # Validate input arguments
        if not args or len(args) < 1 or not args[0]:
            return {"error": "Missing required parameter: picking ID."}

        # Extract picking ID from args
        picking_id = args[0][0] if isinstance(args[0], list) else args[0]

        # Search for the picking record
        picking = request.env['picking.lists'].search([("id", "=", picking_id)])
        if not picking:
            return {"error": "Picking not found with the given ID."}
        # Check the state of the picking record
        if picking.state != 'waiting_pick':
            return {
                "error": "Picking is not in the 'waiting_pick' state.",
                "current_state": picking.state,
            }
        # Attempt to confirm availability
        try:
            picking.action_available()
            return {
                "success": True,
                "message": "Picking availability successfully confirmed.",
                "picking_id": picking_id,
            }
        except ValidationError as e:
            return {
                "error": "Validation error occurred while confirming availability.",
                "message": str(e),
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred.",
                "message": str(e),
                "picking_id": picking_id,
            }


    @http.route('/api/v1/get_picking', cors="*", type='json', auth="user")
    def get_picking(self, args, kwargs):
        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit', 0)
        order = kwargs.get('order', 'id desc')  # Default order by ID descending
        result = []
        args_search = []

        if args[0].get("id"):
            args_search.append(("id", "=", args[0].get("id")))
        else:
            # Handle 'name' search for both name, origin, partner, and sale orders
            name = args[0].get("name")
            if name:
                partner_ids = request.env['res.partner'].search([("name", "ilike", name)]).ids
                so_ids = request.env['sale.order'].search([("name", "ilike", name)]).ids

                if partner_ids or so_ids:
                    conditions = []
                    if partner_ids:
                        conditions.append(("partner_id", "in", partner_ids))
                    if so_ids:
                        conditions.append(("sale_id", "in", so_ids))
                    conditions.append(("name", "ilike", name))
                    conditions.append(("origin", "ilike", name))

                    # Combine the conditions with '|'
                    while len(conditions) > 1:
                        args_search.extend(['|', conditions.pop()])
                    args_search.append(conditions[0])  # Add the final condition
                else:
                    # If no partner or sale order matches, fallback to searching by name and origin only
                    args_search.extend(['|', ("name", "ilike", name), ("origin", "ilike", name)])

            # Add other filters
            if args[0].get("state"):
                args_search.append(("state", "=", args[0].get("state")))
            if args[0].get("picking_date_from"):
                args_search.append(("date", ">=", args[0].get("picking_date_from")))
            if args[0].get("picking_date_to"):
                args_search.append(("date", "<=", args[0].get("picking_date_to")))
            if args[0].get("delivery_date_from"):
                args_search.append(("delivery_date", ">=", args[0].get("delivery_date_from")))
            if args[0].get("delivery_date_to"):
                args_search.append(("delivery_date", "<=", args[0].get("delivery_date_to")))

        picking_ids = request.env['picking.lists'].search(args_search, offset =offset, limit =limit, order =order)
        for pick in picking_ids:
            list_line_ids = []
            for line in pick.list_line_ids:
                list_line_ids.append({
                    "id": line.id,
                    "default_code": line.product_id.default_code,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "tracking": line.product_id.tracking,
                    "sale_id": (line.sale_id.id, line.sale_id.name),
                    "reserved_availability": line.reserved_availability,
                    "qty_ava": line.qty_ava,
                    "qty_all_stock": line.qty_all_stock,
                    "qty": line.qty,
                    "amount_arranged": line.amount_arranged,
                    "qty_done": line.qty_done,
                    "uom_id": (line.uom_id.id, line.uom_id.name),
                    })

            args_attached = [("res_model", "=", "picking.lists"), ("res_id", "=", pick.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)
            sale_ids = []
            for sale in pick.sale_id:
                sale_ids.append({"id":sale.id ,"name":sale.name })
            result.append({
                "id": pick.id,
                "name": pick.name,
                "state": pick.state,
                "partner_id": (pick.partner_id.id, pick.partner_id.name),
                "warehouse_id": (pick.warehouse_id.id, pick.warehouse_id.display_name) ,
                "location_id": (pick.location_id.id, pick.location_id.display_name) ,
                "origin": pick.origin ,
                "sale_id": sale_ids ,
                "date": pick.date,
                "delivery_date": pick.delivery_date,
                "checker": (pick.checker.id, pick.checker.name),
                "user_id": (pick.user_id.id, pick.user_id.name),
                "is_urgent": pick.is_urgent,
                "warehouse_status": pick.warehouse_status,
                "confirm_picking_date": pick.confirm_picking_date,
                "user_confirm_picking": pick.user_confirm_picking,
                "inventory_status": pick.inventory_status,
                "validation_picking_date": pick.validation_picking_date,
                "user_validation_picking": pick.user_validation_picking,
                "project_name": (pick.project_name.id, pick.project_name.project_name),
                "land": pick.land,
                "home": pick.home,
                "room": pick.room,
                "remark": pick.remark,
                "list_line_ids": list_line_ids,
                "attachement": attached,
                })
        return result

    @http.route('/api/v1/update_picking', cors = "*", type = 'json', auth = "user")
    def update_picking(self, args):
        if args:
            for val in args:
                pick = request.env['picking.lists'].browse(val[0])
                list_line_ids = val[1].get("list_line_ids")
                del val[1]["list_line_ids"]
                if pick:
                    pick.write(val[1])
                if list_line_ids:
                    for line in list_line_ids:
                        picking_line = request.env['picking.lists.line'].browse(line[0])
                        picking_line.write(line[1])
                            
            return {
                "success": True,
                "message": "Update successfully.",
                "picking_id": pick.id,
            }
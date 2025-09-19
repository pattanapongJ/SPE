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

class APIReceiptListMaster(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)

    @http.route('/api/v1/get_batch_receipt_list', cors="*", type='json', auth="user")
    def get_batch_receipt_list(self, args, kwargs):
        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit', 0)
        order = kwargs.get('order', 'id desc')  # Default order by ID descending
        result = []
        args_search = []

        if args[0].get("id"):
            args_search.append(("id", "=", args[0].get("id")))
        else:
            if args[0].get("name"):
                args_search.append(("name", "=", args[0].get("name")))
            if args[0].get("partner"):
                partner = args[0].get("partner")
                partner_ids = request.env['res.partner'].search([("name", "ilike", partner)]).ids
                
                if partner_ids:
                    conditions = []
                    if partner_ids:
                        conditions.append(("partner_id", "in", partner_ids))

                    # Combine the conditions with '|'
                    while len(conditions) > 1:
                        args_search.extend(['|', conditions.pop()])
                    args_search.append(conditions[0]) 
            if args[0].get("warehouse"):
                warehouse = args[0].get("warehouse")
                warehouse_id = request.env['stock.warehouse'].search([("name", "=", warehouse)]).id
                if warehouse_id:
                    args_search.append(("warehouse_id", "=", warehouse_id))

            if args[0].get("picking_type"):
                picking_type = args[0].get("picking_type")
                picking_type_data = picking_type.split(',')
                if len(picking_type_data)>1:
                    warehouse = picking_type_data[0]
                    picking_type_name = picking_type_data[1]
                    warehouse_id_picking_type = request.env['stock.warehouse'].search([("name", "=", warehouse)]).id
                    picking_type_ids = request.env['stock.picking.type'].search([("name", "ilike", picking_type_name),("warehouse_id", '=',warehouse_id_picking_type)]).ids
                else:
                    picking_type_name = picking_type_data[0]
                    picking_type_ids = request.env['stock.picking.type'].search([("name", "ilike", picking_type_name)]).ids
    
                if picking_type_ids:
                    conditions = []
                    if picking_type_ids:
                        conditions.append(("picking_type_id", "in", picking_type_ids))

                    # Combine the conditions with '|'
                    while len(conditions) > 1:
                        args_search.extend(['|', conditions.pop()])
                    args_search.append(conditions[0])  # Add the final condition

            # Add other filters
            if args[0].get("state"):
                args_search.append(("state", "=", args[0].get("state")))
            if args[0].get("scheduled_date_from"):
                args_search.append(("scheduled_date", ">=", args[0].get("scheduled_date_from")))
            if args[0].get("scheduled_date_to"):
                args_search.append(("scheduled_date", "<=", args[0].get("scheduled_date_to")))

        batch_ids = request.env['stock.picking.batch'].search(args_search, offset =offset, limit =limit, order =order)

        for batch in batch_ids:
            move_tranfer_ids = []
            move_ids = []
            move_line_tranfer_ids = []
            for line in batch.move_tranfer_ids:
                move_tranfer_ids.append({
                    "id": line.id,
                    "product_id": (line.product_id.id, line.product_id.name),
                    "location_dest_id": (line.location_dest_id.id, line.location_dest_id.complete_name),
                    "reference": line.reference,
                    "origin": line.origin,
                    "date":line.date,
                    "product_uom_qty": line.product_uom_qty,
                    "on_the_way": line.on_the_way,
                    })

            args_attached = [("res_model", "=", "stock.picking.batch"), ("res_id", "=", batch.id)]
            attached = global_api.GET_ATTACHED_FILE(args_attached)
            dict_data = {
                "id": batch.id,
                "name": batch.name,
                "state": batch.state,
                "partner_id": (batch.partner_id.id, batch.partner_id.name),
                "user_id":(batch.user_id.id,batch.user_id.name),
                "picking_type_id":(batch.picking_type_id.id,batch.picking_type_id.name),
                "company_id":(batch.company_id.id,batch.company_id.name),
                "origin_country":(batch.origin_country.id,batch.origin_country.name),
                "shipping_provider":(batch.shipping_provider.id,batch.shipping_provider.name),
                "invoice_no": batch.invoice_no,
                "scheduled_date":batch.scheduled_date,
                "warehouse_status": batch.warehouse_status,
                "bill_status": batch.bill_status,
                "etd": batch.etd,
                "eta": batch.eta,
                "wh_date": batch.wh_date,
                "delivery_mode":(batch.delivery_mode.id,batch.delivery_mode.name),
                "origin": batch.origin,
                "move_tranfer_ids": move_tranfer_ids,
                }
            if batch.state != 'draft':
                for line2 in batch.move_ids:
                    move_ids.append({
                        "id": line2.id,
                        "product_id": (line2.product_id.id, line2.product_id.name),
                        "picking_id":(line2.picking_id.id, line2.picking_id.name),
                        "product_uom_qty": line2.product_uom_qty,
                        "reserved_availability": line2.reserved_availability,
                        "quantity_done": line2.quantity_done,
                        "product_uom": (line2.product_uom.id, line2.product_uom.name),
                        })
                for line3 in batch.move_line_tranfer_ids:
                    move_line_tranfer_ids.append({
                        "id": line3.id,
                        "product_id": (line3.product_id.id, line3.product_id.name),
                        "picking_id":(line3.picking_id.id, line3.picking_id.name),
                        "lot_id":(line3.lot_id.id, line3.lot_id.name),
                        "location_id": (line3.location_id.id, line3.location_id.complete_name),
                        "location_dest_id": (line3.location_dest_id.id, line3.location_dest_id.complete_name),
                        "product_uom_qty": line3.product_uom_qty,
                        "product_uom_id": (line3.product_uom_id.id, line3.product_uom_id.name),
                        "qty_done": line3.qty_done,
                        "company_id":(line3.company_id.id,line3.company_id.name),
                        })
                dict_data["move_ids"] = move_ids
                dict_data["move_line_tranfer_ids"] = move_line_tranfer_ids
            dict_data["attachement"] = attached
            result.append(dict_data)

        return result

    @http.route('/api/v1/update_batch_receipt_list', cors = "*", type = 'json', auth = "user")
    def update_batch_receipt_list(self, args):
        if args:
            for val in args:
                batch = request.env['stock.picking.batch'].browse(val[0])
                if batch.state == 'draft':
                    move_tranfer_ids = val[1].get("move_tranfer_ids")
                    if move_tranfer_ids:
                        for line in move_tranfer_ids:
                            move_tranfer_line = request.env['stock.move'].browse(line[0])
                            move_tranfer_line.write(line[1])

                elif batch.state == 'in_progress':
                    move_line_tranfer_ids = val[1].get("move_line_tranfer_ids")
                    if move_line_tranfer_ids:
                        for line2 in move_line_tranfer_ids:
                            move_line_tranfer_id_line = request.env['stock.move.line'].browse(line2[0])
                            move_line_tranfer_id_line.write(line2[1])

                del val[1]["move_tranfer_ids"]
                del val[1]["move_line_tranfer_ids"]

                if batch:
                    batch.write(val[1])
             
            return {
                "success": True,
                "message": "Update successfully.",
                "batch_id": batch.id,
            }
    
    @http.route('/api/v1/confirm_batch_receipt_list', cors="*", type='json', auth="user")
    def confirm_batch_receipt_list(self, **kwargs):
        # Extract `args` from `kwargs`
        args = kwargs.get("args", [])
        
        # Validate that args[0] is provided
        if not args or len(args) < 1 or not args[0]:
            return {"error": "Missing required parameter: Receipt list ID."}

        # Search for the Receipt list record
        batch_id = args[0][0] if isinstance(args[0], list) else args[0]
        batch = request.env['stock.picking.batch'].search([("id", "=", batch_id)])
        
        if not batch:
            return {"error": "Receipt list not found with the given ID."}
        if batch.state != 'draft':
            return {
                "error": "Receipt list is not in the 'draft' state.",
                "current_state": batch.state,
            }
        
        try:
            # Call action_confirm and handle any validation errors
            batch.action_confirm()
            return {
                "success": True,
                "message": "Receipt list confirmed successfully.",
                "batch_id": batch_id,
            }
        except ValidationError as e:
            # Return a detailed validation error message
            return {
                "error": "Validation error occurred.",
                "message": str(e),
                "batch_id": batch_id
            }
        except UserError as e:
            # Handle user-specific errors gracefully
            return {
                "error": "UserError error occurred.",
                "message": str(e),
                "batch_id": batch_id
            }
        except Exception as e:
            # Catch unexpected exceptions for debugging
            return {
                "error": True,
                "message": "An unexpected error occurred.",
                "batch_id": batch_id
            }
        
    @http.route('/api/v1/confirm_warehouse_batch_receipt_list', cors="*", type='json', auth="user")
    def confirm_warehouse_batch_receipt_list(self, **kwargs):
        # Extract `args` from `kwargs`
        args = kwargs.get("args", [])
        
        # Validate that args[0] is provided
        if not args or len(args) < 1 or not args[0]:
            return {"error": "Missing required parameter: Receipt list ID."}

        # Search for the Receipt list record
        batch_id = args[0][0] if isinstance(args[0], list) else args[0]
        batch = request.env['stock.picking.batch'].search([("id", "=", batch_id)])
        
        if not batch:
            return {"error": "Receipt list not found with the given ID."}
        if batch.state != 'in_progress':
            return {
                "error": "Receipt list is not in the 'in_progress' state.",
                "current_state": batch.state,
            }
        
        try:
            # Call action_confirm and handle any validation errors
            batch.action_confirm_warehouse_batch()
            return {
                "success": True,
                "message": "Receipt list confirmed warehouse successfully.",
                "batch_id": batch_id,
            }
        except ValidationError as e:
            # Return a detailed validation error message
            return {
                "error": "Validation error occurred.",
                "message": str(e),
                "batch_id": batch_id
            }
        except UserError as e:
            # Handle user-specific errors gracefully
            return {
                "error": "UserError error occurred.",
                "message": str(e),
                "batch_id": batch_id
            }
        except Exception as e:
            # Catch unexpected exceptions for debugging
            return {
                "error": True,
                "message": "An unexpected error occurred.",
                "batch_id": batch_id
            }
        
    @http.route('/api/v1/cancel_batch_receipt_list', cors = "*", type = 'json', auth = "user")
    def cancel_batch_receipt_list(self, args):
        if not args or not args[0]:
            return {"error": "Missing required parameter: Receipt list ID."}

        batch_id = args[0][0] if isinstance(args[0], list) else args[0]
        batch = request.env['stock.picking.batch'].search([("id", "=", batch_id)])
        if not batch:
            return {"error": "Receipt list not found with the given ID."}

        try:
            batch.action_cancel()
            return {
                "success": True,
                "message": "Receipt list Cancel successfully.",
                "batch_id": batch_id,
            }
        except ValidationError as e:
            return {
                "error": "Validation error occurred.",
                "message": str(e),
                "batch_id": batch_id
            }
        except UserError as e:
            # Handle user-specific errors gracefully
            return {
                "error": "UserError error occurred.",
                "message": str(e),
                "picking_id": batch_id
            }
        except Exception as e:
            return {
                "error": "An unexpected error occurred.",
                "message": str(e),
                "picking_id": batch_id,
            }
    
    def button_validate_batch_receipt_list(self, args):
        get_receipt_list = request.env['stock.picking.batch'].search([('id', '=', args)])
        data = get_receipt_list.action_done()
        if data != None:
            if get_receipt_list:
                if data.get('name') == "Create Backorder?":
                    backorder_confirmation_line_ids = []
                    pick_ids_backorder_data = []
                    pickings_to_validate_ids = []
                    pick_ids_backorder = data.get('context').get('default_pick_ids')
                    for pick_id in pick_ids_backorder:
                        pick_ids_backorder_data.append(pick_id[1])
   
                    button_validate_picking_ids = data.get('context').get('button_validate_picking_ids') 
                    for picking in button_validate_picking_ids:
                        pickings_to_validate_ids.append((4,picking))
                        if picking in pick_ids_backorder_data:
                            backorder_confirmation_line_ids.append((0, 0, {'to_backorder': True, 'picking_id': picking}))

                    picking = request.env['stock.backorder.confirmation'].create({
                        'pick_ids': data.get('context').get('default_pick_ids'), 'backorder_confirmation_line_ids': backorder_confirmation_line_ids,
                        'batch_id':get_receipt_list.id,'pickings_to_validate_ids':pickings_to_validate_ids,
                        })
                    return {"id": picking.id, "batch_id": get_receipt_list.id, "massage": data.get('name')}
        else:
            return True
    
    @http.route('/api/v1/validate_batch_receipt_list', cors = "*", type = 'json', auth = "user")
    def validate_batch_receipt_list(self, args):
        return self.button_validate_batch_receipt_list(args)
    
    @http.route('/api/v1/confirm_backorder_batch_receipt_list', cors="*", type='json', auth="user")
    def confirm_backorder_batch_receipt_list(self, **kwargs):
        args = kwargs.get("args", [])
        if not args or not args[0]:
            return {"error": "Missing required parameter: Receipt list backorder ID."}

        batch_backorder = request.env['stock.backorder.confirmation'].search([("id", "=", args[0])])
        if not batch_backorder:
            return {"error": "Picking list not found with the given ID."}

        try:
            batch_backorder.process()
            batch = request.env['stock.picking.batch'].search([('origin', '=', batch_backorder.batch_id.name)])
            return {
                "success": True,
                "message": "Receipt list backorder created successfully.",
                "backorder_ids": batch.id,
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
        
    @http.route('/api/v1/confirm_nobackorder_batch_receipt_list', cors="*", type='json', auth="user")
    def confirm_nobackorder_batch_receipt_list(self, **kwargs):
        args = kwargs.get("args", [])
        if not args or not args[0]:
            return {"error": "Missing required parameter: Receipt list backorder ID."}

        batch_backorder = request.env['stock.backorder.confirmation'].search([("id", "=", args[0])])
        if not batch_backorder:
            return {"error": "Picking list not found with the given ID."}

        try:
            batch_backorder.process_cancel_backorder()
            return {
                "success": True,
                "message": "Receipt list confirmed without backorder.",
                "backorder_ids": batch_backorder.batch_id.id,
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
        

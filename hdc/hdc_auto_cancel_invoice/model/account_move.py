# Copyright 2009-2018 Noviat
# Copyright 2021 Tecnativa - João Marques
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class AccountMove(models.Model):
    _inherit = "account.move"

    def cancel_entry_auto_button(self):        
        return {
                "name": "Confirmation",
                "type": "ir.actions.act_window",
                "res_model": "wizard.auto.confirm",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_account_id": self.id},
            }

    def cancel_entry_auto(self):

        self.ensure_one()
        for picking in self.picking_ids:
            picking_done = picking.filtered(lambda x: x.state == 'done' and x.picking_type_id.code == 'outgoing' and x.order_return == 0)
 
            if picking and not self.sale_type_id.is_retail:

                picking_from_invoice = picking

                picking_list_line = self.env["picking.lists.line"].search(
                    [("picking_id", "=", picking.id), ("state", "!=", "cancel")],
                )  # ไปหามาว่าใน picking list line ไหนบ้างที่มีข้อมูลของใบ picking นี้ แล้ว state ไม่ใช่ cancel
                
                if picking_list_line:

                    keep_picking_list = set()
                    keep_sale_order = set()

                    for pk_line in picking_list_line:

                        # change state line to red color -> chanve State to Cancel
                        pk_line.state_cancel = True

                        # first Check this is have multi sale order?
                        keep_picking_list.add(pk_line.picking_lists)  # Keep Picking List

                        keep_sale_order.add(pk_line.sale_id)

                    
                    # Loop Picking List for set Cancel Picking List if in line is all state 'cancel'
                    keep_picking_list = list(keep_picking_list)
                    for each_pkl in keep_picking_list:
                        all_lines_cancelled = all(line.state == 'cancel' for line in each_pkl.list_line_ids)

                        if all_lines_cancelled:
                            each_pkl.state = 'cancel'

                    # Loop Sale Order for go to create Return
                    keep_sale_order = list(keep_sale_order)
                    for each_so in keep_sale_order:

                        sale_order_id = each_so

                        if each_so.state in ['sale', 'done'] and each_so.delivery_count > 0: # Check Have Delivery                            

                            sale_order_cancel = self.env["sale.order.cancel"]

                            reason_id = self.env["sale.order.cancel.reason"].search(
                                [("name", "=", "บันทึกจำนวนสินค้าผิด")]
                            ) or self.env["sale.order.cancel.reason"].search([], limit=1)

                            wizard = sale_order_cancel.create(
                                {
                                    "reason_id": reason_id.id,
                                    "order_id": each_so.id,
                                }
                            )

                            wizard.action_cancel()  # Cancel Sale Order
                    
                            if each_so.picking_ids:

                                # Check Case Back Order
                                check_picking_lists = self.env['picking.lists.line'].search([('sale_id', '=', each_so.id)])
                                list_picking_lists = list(set(check_picking_lists.mapped('picking_lists')))
                                for l_pk_l_main in list_picking_lists:
                                    if l_pk_l_main.state != 'cancel':
                                        for l_pk_l in l_pk_l_main.list_line_ids:
                                            if l_pk_l.sale_id.id == sale_order_id.id:
                                                l_pk_l.state_cancel = True
                                    check_all_lines_cancelled = all(line.state == 'cancel' for line in l_pk_l_main.list_line_ids)
                                    if check_all_lines_cancelled:
                                        l_pk_l_main.state = 'cancel'

                                delivery_ids = each_so.picking_ids  # Go To Delivery

                                for delivery_id in delivery_ids:

                                    if delivery_id.id == picking_from_invoice.id:
                                        
                                        if delivery_id.state == "done":

                                            # Create Wizard Return
                                            return_picking_wizard = (
                                                self.env["stock.return.picking"]
                                                .with_context(active_id=delivery_id.id)
                                                .create(
                                                    {
                                                        "picking_id": delivery_id.id,
                                                        "remark": "คืนสินค้า",
                                                    }
                                                )
                                            )

                                            # Add Location ID
                                            if delivery_id.location_id:
                                                return_picking_wizard.write(
                                                    {"location_id": delivery_id.location_id.id}
                                                )

                                            return_picking_wizard._onchange_picking_id()

                                            # Create Return
                                            result_result = (
                                                return_picking_wizard.create_returns()
                                            )

                                            # Return Create
                                            if result_result:

                                                # Find Picking
                                                res_id = result_result.get("res_id")
                                                res_model = result_result.get("res_model")

                                                # Check For Find Picking
                                                if res_id and res_model:
                                                    pick = self.env[res_model].browse(res_id)
                                                    pick.action_confirm_warehouse()
                                                    pick.button_validate()
                                        else:
                                            delivery_id.state == "cancel"

                    # -----------------------------------------------------------------

                    # # change state line to red color -> chanve State to Cancel
                    # picking_list_line.state_cancel = True             

                    # # first Check this is have multi sale order?
                    # picking_list_id = picking_list_line.picking_lists  # Picking List

                    # # Check Number of Sale Order
                    # sale_order_ids = {line.sale_id.id for line in picking_list_id.list_line_ids}

                    # # Case 1 PL 1 SO
                    # if len(sale_order_ids) == 1:
                    #     picking_list_id.state = "cancel"

                    # # Case 1 PL ,SO > 1
                    # if len(sale_order_ids) > 1:
                    #     all_lines_cancelled = all(line.state == 'cancel' for line in picking_list_id.list_line_ids)

                    #     # Every Record is cancel
                    #     if all_lines_cancelled:
                    #         picking_list_id.state = "cancel"

                    # if picking_list_line.sale_id:

                    #     # Go to SO
                    #     sale_order_id = picking_list_line.sale_id  # Sale Order

                    #     if sale_order_id.state == 'sale':

                    #         sale_order_cancel = self.env["sale.order.cancel"]

                    #         reason_id = self.env["sale.order.cancel.reason"].search(
                    #             [("name", "=", "บันทึกจำนวนสินค้าผิด")]
                    #         ) or self.env["sale.order.cancel.reason"].search([], limit=1)

                    #         wizard = sale_order_cancel.create(
                    #             {
                    #                 "reason_id": reason_id.id,
                    #                 "order_id": sale_order_id.id,
                    #             }
                    #         )

                    #         wizard.action_cancel()  # Cancel Sale Order

                    #         if sale_order_id.picking_ids:

                    #             delivery_ids = sale_order_id.picking_ids  # Go To Delivery

                    #             for delivery_id in delivery_ids:

                    #                 if delivery_id.id == picking.id and delivery_id.state == "done":

                    #                     # Create Wizard Return
                    #                     return_picking_wizard = (
                    #                         self.env["stock.return.picking"]
                    #                         .with_context(active_id=delivery_id.id)
                    #                         .create(
                    #                             {
                    #                                 "picking_id": delivery_id.id,
                    #                                 "remark": "คืนสินค้า",
                    #                             }
                    #                         )
                    #                     )

                    #                     # Add Location ID
                    #                     if delivery_id.location_id:
                    #                         return_picking_wizard.write(
                    #                             {"location_id": delivery_id.location_id.id}
                    #                         )

                    #                     return_picking_wizard._onchange_picking_id()

                    #                     # Create Return
                    #                     result_result = (
                    #                         return_picking_wizard.create_returns()
                    #                     )

                    #                     # Return Create
                    #                     if result_result:

                    #                         # Find Picking
                    #                         res_id = result_result.get("res_id")
                    #                         res_model = result_result.get("res_model")

                    #                         # Check For Find Picking
                    #                         if res_id and res_model:
                    #                             pick = self.env[res_model].browse(res_id)
                    #                             pick.action_confirm_warehouse()
                    #                             pick.button_validate()

                    #                 else:

                    #                     delivery_id.state == "cancel"
                elif picking_done and self.sale_type_id.is_retail:

                    return_picking_wizard = self.env['stock.return.picking'].with_context(active_id=picking_done.id).create(
                        {'picking_id': picking_done.id , 'remark': "คืนสินค้า"}
                        )
                    
                    if picking_done.location_id:
                        return_picking_wizard.write({'location_id': picking_done.location_id.id})

                    return_picking_wizard._onchange_picking_id()

                    result_result = return_picking_wizard.create_returns()

                    # Return Create Fail
                    if not result_result:
                        pass

                    # Find Picking
                    res_id = result_result.get('res_id')
                    res_model = result_result.get('res_model')

                    # Cannot Find Picking
                    if not res_id and not res_model:
                        pass          
                    
                    result_picking = self.env[res_model].browse(res_id)

                    # Cannot Find Picking
                    if not result_picking:
                        pass

                    data = result_picking.button_validate()

                    try:
                        if data.get('name') == "Immediate Transfer?" or data.get('res_model') == 'stock.immediate.transfer':
                            immediate_transfer = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, result_picking.id)], 'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': result_picking.id})]})
                            if immediate_transfer:
                                immediate_transfer.process() # force Done
                                result_picking.button_validate()
                        else:
                            raise UserError(
                                _(
                                    "ระบบไม่สามารถยืนยันรับสินค้าได้"
                                )
                            )
                    except:
                        pass
                    sale_order_cancel = self.env["sale.order.cancel"]

                    reason_id = self.env["sale.order.cancel.reason"].search(
                        [("name", "=", "บันทึกจำนวนสินค้าผิด")]
                    ) or self.env["sale.order.cancel.reason"].search([], limit=1)
                    wizard = sale_order_cancel.create(
                        {
                            "reason_id": reason_id.id,
                            "order_id": picking_done.sale_id.id,
                        }
                    )
                    wizard.action_cancel() 
        self.button_cancel() # Cancel Invoice


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

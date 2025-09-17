odoo.define('hdc_inventory_adj_confirm.inventory_line_button_control', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session'); // นำเข้า session สำหรับตรวจสอบกลุ่มผู้ใช้

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            var self = this;
            session.user_has_group('hdc_inventory_adj_confirm.group_inventory_adj').then(function (hasGroup) {
                if (!hasGroup) {
                    // ซ่อนปุ่มทันทีหากผู้ใช้ไม่ได้อยู่ในกลุ่ม
                    self.$buttons.find('.o_button_validate_inventory').hide();
                    return;
                }
                // ดึงข้อมูล ids ของ stock.inventory.line ผ่าน model
                var recordIds = self.model.get(self.handle, { raw: true }).res_ids;

                if (recordIds && recordIds.length > 0) {
                    rpc.query({
                        model: 'stock.inventory.line',
                        method: 'search_read',
                        args: [[['id', 'in', recordIds]]],
                        fields: ['inventory_id'],
                        limit: 1,
                    }).then(function (inventoryLines) {
                        if (inventoryLines.length > 0) {
                            var inventory_id = inventoryLines[0].inventory_id[0]; // ดึง ID ของ stock.inventory
                            // ใช้ inventory_id ดึงค่า inventory_status
                            rpc.query({
                                model: 'stock.inventory',
                                method: 'read',
                                args: [[inventory_id], ['inventory_status']],
                            }).then(function (inventories) {
                                if (inventories.length > 0 && inventories[0].inventory_status === 'waiting') {
                                    // ซ่อนปุ่ม Validate Inventory ถ้า inventory_status เป็น warehouse
                                    self.$buttons.find('.o_button_validate_inventory').hide();
                                }
                            });
                        }
                    });
                }
            });
        },
    });
});

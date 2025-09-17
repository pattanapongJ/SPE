odoo.define('hdc_discount.hide_gb_line', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var fieldRegistry = require('web.field_registry');
    var SectionAndNoteOne2Many = require('sale.SectionAndNoteFieldOne2Many'); // เรียกใช้ widget เดิม

    // ขยาย ListRenderer เพื่อเพิ่มฟังก์ชันใหม่
    var HideGbLineRenderer = ListRenderer.extend({
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._hideDiscountLines();
                self._setupEventListeners();
            });
        },
        _hideDiscountLines: function () {
            var self = this;
            self.$el.find('tr.o_data_row').each(function () {
                var recordId = $(this).data('id');
                var record = self.state.data.find(record => record.id === recordId);
                
                // ซ่อนแถวถ้าเป็น global discount หรือ downpayment
                if (record && (record.data.is_global_discount || record.data.is_downpayment)) {
                    $(this).hide();
                }
            });
        },
        _setupEventListeners: function () {
            var self = this;
            this.$el.on('change', 'tr.o_data_row input, tr.o_data_row select', function () {
                self._hideDiscountLines();
            });

            // สังเกตการเปลี่ยนแปลงในตาราง
            var observer = new MutationObserver(function (mutations) {
                mutations.forEach(function () {
                    self._hideDiscountLines();
                });
            });

            // สังเกตการเปลี่ยนแปลงในโครงสร้างของตาราง
            observer.observe(this.$el[0], { childList: true, subtree: true });
        },
    });

    // ขยาย widget section_and_note_one2many
    var HideGbLine = SectionAndNoteOne2Many.extend({
        _getRenderer: function () {
            return HideGbLineRenderer;
        }
    });

    fieldRegistry.add('hide_gb_line', HideGbLine); // ลงทะเบียน widget ใหม่

    return HideGbLine;
});

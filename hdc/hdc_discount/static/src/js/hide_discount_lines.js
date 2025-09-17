odoo.define('hdc_discount.hide_gb_line', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var fieldRegistry = require('web.field_registry');
    var One2ManyList = require('web.relational_fields').FieldOne2Many;

    var HideGbLineRenderer = ListRenderer.extend({
        _renderBodyCell: function (record, node, index, options) {
            var $cell = this._super.apply(this, arguments);
    
            var isSection = record.data.display_type === 'line_section';
            var isNote = record.data.display_type === 'line_note';
    
            if (isSection || isNote) {
                if (node.attrs.widget === "handle") {
                    return $cell;
                } else if (node.attrs.name === "name") {
                    var nbrColumns = this._getNumberOfCols();
                    if (this.handleField) {
                        nbrColumns--;
                    }
                    if (this.addTrashIcon) {
                        nbrColumns--;
                    }
                    $cell.attr('colspan', nbrColumns);
                } else {
                    $cell.removeClass('o_invisible_modifier');
                    return $cell.addClass('o_hidden');
                }
            }
    
            return $cell;
        },
        _renderRow: function (record, index) {
            var $row = this._super.apply(this, arguments);
    
            if (record.data.display_type) {
                $row.addClass('o_is_' + record.data.display_type);
            }
    
            return $row;
        },
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.$('.o_list_table').addClass('o_section_and_note_list_view');
                self._hideDiscountLines();
                self._setupEventListeners();
            });
        },
        _hideDiscountLines: function () {
            var self = this;
            self.$el.find('tr.o_data_row').each(function () {
                var recordId = $(this).data('id');
                var record = self.state.data.find(record => record.id === recordId);
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

            // Create an observer to watch for changes in the table
            var observer = new MutationObserver(function (mutations) {
                mutations.forEach(function () {
                    self._hideDiscountLines();
                });
            });

            // Observe the table for changes
            observer.observe(this.$el[0], { childList: true, subtree: true });
        },
    });

    var HideGbLine = One2ManyList.extend({
        _getRenderer: function () {
            return HideGbLineRenderer;
        }
    });

    fieldRegistry.add('hide_gb_line', HideGbLine);

    return HideGbLine;
});

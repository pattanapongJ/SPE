odoo.define('hdc_product_kit.hide_component_line', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var fieldRegistry = require('web.field_registry');
    var One2ManyList = require('web.relational_fields').FieldOne2Many;

    var HideGbLineRenderer = ListRenderer.extend({
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._hideComponent();
                self._setupEventListeners();
            });
        },
        _hideComponent: function () {
            var self = this;
            self.$el.find('tr.o_data_row').each(function () {
                var recordId = $(this).data('id');
                var record = self.state.data.find(record => record.id === recordId);
                if (record && record.data.is_component) {
                    $(this).hide();
                }
            });
        },
        _setupEventListeners: function () {
            var self = this;
            this.$el.on('change', 'tr.o_data_row input, tr.o_data_row select', function () {
                self._hideComponent();
            });

            // Create an observer to watch for changes in the table
            var observer = new MutationObserver(function (mutations) {
                mutations.forEach(function () {
                    self._hideComponent();
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

    fieldRegistry.add('hide_component_line', HideGbLine);

    return HideGbLine;
});

odoo.define('search_purchase_forecast_tree_view_header_buttons.tree_view_button', function (require){
  "use strict";

  var ListController = require('web.ListController');
  var viewUtils = require('web.viewUtils');

  function renderSearchPurchaseForecastButton() {
      if (this.$buttons) {
          var self = this;
          this.$buttons.on('click', '.o_button_search_purchase_forecast', function () {
              self.do_action({
                  name: 'Searching Purchase Forecast',
                  type: 'ir.actions.act_window',
                  res_model: 'search.forecast.purchase',
                  views: [[false, 'form']],
              });
          });
      }
  }
  ListController.include({
      renderButtons: function ($node) {
          this._super.apply(this, arguments);
          renderSearchPurchaseForecastButton.apply(this, arguments);
      },
  });
});
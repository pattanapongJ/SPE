odoo.define("bs_internal_account_statement_report.client_action", function (require) {
    "use strict";

    var ReportAction = require("report.client_action");
    var core = require("web.core");

    var QWeb = core.qweb;

    const AFRReportAction = ReportAction.extend({
        start: function () {
            return this._super.apply(this, arguments).then(() => {
                this.$buttons = $(
                    QWeb.render(
                        "bs_internal_account_statement_report.client_action.ControlButtons",
                        {}
                    )
                );
                this.$buttons.on("click", ".o_report_print", this.on_click_print);

                this.controlPanelProps.cp_content = {
                    $buttons: this.$buttons,
                };

                this._controlPanelWrapper.update(this.controlPanelProps);
            });
        },

    });

    core.action_registry.add("bs_internal_account_statement_report.client_action", AFRReportAction);

    return AFRReportAction;
});

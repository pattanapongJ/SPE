odoo.define('bs_pw_partial_payment_reconcile.account_payment', function (require) {
    let ShowPaymentLineWidget = require('account.payment').ShowPaymentLineWidget;
    var field_utils = require('web.field_utils');

    ShowPaymentLineWidget.include({
        /**
         * Override to preprocess dates before rendering.
         */
        _render: function () {
            // Call parent method
            this._super.apply(this, arguments);

            const info = JSON.parse(this.value);
            if (!info) {
                this.$el.html('');
                return;
            }

            // Preprocess reconcile_date to format it
            _.each(info.content, function (line) {
                if (line.reconcile_date) {
                    line.reconcile_date = field_utils.format.date(
                        field_utils.parse.date(line.reconcile_date, {}, {isUTC: true})
                    );
                    console.log(line.reconcile_date)
                }
            });


            this.$('.js_payment_info').each(function (index, element) {
                const line = info.content[index];
                if (line && line.reconcile_date) {
                     $(element).after(
                            `<i class="reconcile-date" style="margin-right:3px;">${line.reconcile_date}</i>`
                        );
                }
            });
        },


    });
    return ShowPaymentLineWidget;
});

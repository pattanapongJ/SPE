odoo.define('bs_billing_add.HideDeleteBtn', function (require){
    "use strict";

    var ListController = require('web.ListController');
    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({
        _getActionMenuItems: function (state) {
            if (!this.hasActionMenus || this.mode === 'edit') {
                return null;
            }
            const props = this._super(...arguments);
         
            if (this.modelName === 'account.billing') {
                if (state.data.state === 'billed') {
                    const otherActionItems = props.items.other.filter(item => {
                        return item.description !== _t("Delete");
                    });
        
                    return Object.assign({}, props, {
                        items: Object.assign({}, props.items, { other: otherActionItems }),
                    });
                }
            }
            return props;
        },
    });

    ListController.include({
        _getActionMenuItems: function (state) {
            if (!this.hasActionMenus || !this.selectedRecords.length) {
                return null;
            }
            const props = this._super(...arguments);

            if (this.modelName === 'account.billing') {
                let states = state.data;
                for (let i = 0; i < states.length; i++) {
                    state = states[i].data.state;
                    if (state === 'billed') {
                        const otherActionItems = props.items.other.filter(item => {
                            return item.description !== _t("Delete");
                        });
            
                        return Object.assign({}, props, {
                            items: Object.assign({}, props.items, { other: otherActionItems }),
                        });
                    }
                    
                }
            }
            return props;
        },
    });
    
});
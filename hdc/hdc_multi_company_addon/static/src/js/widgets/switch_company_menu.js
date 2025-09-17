odoo.define('web.HDCSwitchCompanyMenu', function(require) {
    "use strict";
    
    /**
     * When Odoo is configured in multi-company mode, users should obviously be able
     * to switch their interface from one company to the other.  This is the purpose
     * of this widget, by displaying a dropdown menu in the systray.
     */
    
    var config = require('web.config');
    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    
    var _t = core._t;
    
    var HDCSwitchCompanyMenu = Widget.extend({
        template: 'HDCSwitchCompanyMenu',
        events: {
            'click .dropdown-item[data-menu] div.log_into': '_onSwitchCompanyClick',
            'keydown .dropdown-item[data-menu] div.log_into': '_onSwitchCompanyClick',
            'click .dropdown-item[data-menu] div.toggle_company': '_onToggleCompanyClick',
            'keydown .dropdown-item[data-menu] div.toggle_company': '_onToggleCompanyClick',
        },
        // force this item to be the first one to the left of the UserMenu in the systray
        sequence: 1,
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this.isMobile = config.device.isMobile;
            this._onSwitchCompanyClick = _.debounce(this._onSwitchCompanyClick, 1500, true);
            this.isMultiCompanyAll = false;
            this.isMultiCompanyUnique = false;
        },
    
        /**
         * @override
         */
        willStart: function () {
            var self = this;
            this.allowed_company_ids = String(session.user_context.allowed_company_ids)
                                        .split(',')
                                        .map(function (id) {return parseInt(id);});
            this.user_companies = session.user_companies.allowed_companies;
            this.current_company = this.allowed_company_ids[0];
            this.current_company_name = _.find(session.user_companies.allowed_companies, function (company) {
                return company[0] === self.current_company;
            })[1];
            var readyAll = this.getSession().user_has_group('hdc_multi_company_addon.group_multi_company_all').then(function(has_group) {
                self.isMultiCompanyAll = has_group;
            });
            var readyUnique = this.getSession().user_has_group('hdc_multi_company_addon.group_multi_company_unique').then(function(has_group) {
                self.isMultiCompanyUnique = has_group;
            });
            
            return Promise.all([this._super.apply(this, arguments),readyAll,readyUnique]);
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onSwitchCompanyClick: function (ev) {
            if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var dropdownMenu = dropdownItem.parent();
            var companyID = dropdownItem.data('company-id');
            var allowed_company_ids = this.allowed_company_ids;
            if (this.isMultiCompanyUnique && !this.isMultiCompanyAll){
                allowed_company_ids = [companyID];
            }
            if (dropdownItem.find('.fa-square-o').length) {
                // 1 enabled company: Stay in single company mode
                if (this.allowed_company_ids.length === 1) {
                    if (this.isMobile) {
                        dropdownMenu = dropdownMenu.parent();
                    }
                    dropdownMenu.find('.fa-check-square').removeClass('fa-check-square').addClass('fa-square-o');
                    dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                    allowed_company_ids = [companyID];
                } else { // Multi company mode
                    if(this.isMultiCompanyAll){
                        allowed_company_ids.push(companyID);
                    }
                    dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                }
            }
            $(ev.currentTarget).attr('aria-pressed', 'true');
            session.setCompanies(companyID, allowed_company_ids);
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @param {MouseEvent|KeyEvent} ev
         */
        _onToggleCompanyClick: function (ev) {
            if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var companyID = dropdownItem.data('company-id');
            var allowed_company_ids = this.allowed_company_ids;
            var current_company_id = allowed_company_ids[0];
            if (this.isMultiCompanyUnique && !this.isMultiCompanyAll){
                allowed_company_ids = [companyID];
            }
            if (dropdownItem.find('.fa-square-o').length) {
                if(this.isMultiCompanyAll){
                    allowed_company_ids.push(companyID);
                }
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'true');
            } else {
                allowed_company_ids.splice(allowed_company_ids.indexOf(companyID), 1);
                dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
                $(ev.currentTarget).attr('aria-checked', 'false');
            }
            session.setCompanies(current_company_id, allowed_company_ids);
        },
    
    });
    
    if (session.display_switch_company_menu) {
        SystrayMenu.Items.push(HDCSwitchCompanyMenu);
    }
    
    return HDCSwitchCompanyMenu;
    
    });
    
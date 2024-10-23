odoo.define('account_plaid.acc_config_widget', function(require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var common = require('web.form_common');
var Model = require('web.Model');
var framework = require('web.framework');
var online_sync = require('account_online_sync.acc_config_widget');
var QWeb = core.qweb;
var AbstractAction = require('web.Widget');

var PlaidAccountEndResult = AbstractAction.extend({
    template: 'Success',
    events: {
        'click .js_process_cancel': 'closeModal',
    },
    closeModal: function(event) {
        this.do_action({type: 'ir.actions.act_window_close'});
    },
    init: function(parent, context) {
        this._super(parent, context);
        this.init_call = context.context.init_call;
        // Account won't be added afterwards with new api
        this.number_added = 0;
        this.transactions = context.context.transactions;
    },
    renderElement: function() {
        var $el;
        var local = {init_call: this.init_call, transactions: this.transactions};
        $el = $(QWeb.render(this.template, local).trim());
        this.replaceElement($el);
    },
});

var PlaidAccountConfigurationWidget = AbstractAction.extend({
    on_attach_callback: function () {
        if (this.exit === true) {
            this.do_action({type: 'ir.actions.act_window_close'});
        }
    },
    init: function(parent, context) {
        this._super(parent, context);
        var self = this;
        this.context = context.context;
        this.exit = false;
        this.loaded = $.Deferred();
        this.institution_id = context.institution_id;
        this.plaid_link = context.open_link;
        this.account_online_provider_id = context.account_online_provider_id;
        this.public_key = context.public_key;
        this.public_token = context.public_token;
        if (context.result) {
            this.result = context.result;
        }
    },
    
    willStart: function() {
        var self = this;
        if (this.plaid_link === true) {
            ajax.loadJS('https://cdn.plaid.com/link/v2/stable/link-initialize.js')
                .then(function() {
                    var plaid_options = {
                        clientName: 'Odoo',
                        env: 'production',
                        key: self.public_key,
                        product: ['transactions'],
                        onSuccess: function(public_token, metadata) {
                            if (self.public_token === undefined) {
                                return self.linkSuccess(public_token, metadata);
                            }
                            else {
                                self.exit = true;
                                // This is needed since on_attach_callback does not exists in this version
                                window.location.reload();
                                self.destroy();
                            }
                        },
                        onExit: function(err, metadata) {
                            if (err) {
                                console.log(err);
                                console.log(metadata);
                            }
                            self.exit = true;
                            window.location.reload();
                            self.destroy();
                        },
                    }
                    if (self.public_token !== undefined) {
                        plaid_options['token'] = self.public_token;
                    }
                    self.plaid_link = Plaid.create(plaid_options);
                    // Open link in update mode for a specific item
                    if (self.public_token !== undefined) {
                        self.plaid_link.open();
                    }
                    else {
                        // Open link in create mode with the institution id as parameter
                        // in order to open directly on that institution
                        self.plaid_link.open(self.institution_id);
                    }
                });
        }
        else {
            // Just show how many transactions have been fetched
            this.loaded.resolve();
        }
        return this.loaded;
    },

    linkSuccess: function(public_token, metadata) {
        var self = this;
        return new Model('account.online.provider')
            .call('link_success', [[self.id], public_token, metadata, self.context])
            .then(function(result) {
                self.do_action(result);
            });
    },

    renderElement: function() {
        var self = this;
        if (this.exit === true) {
            return this._super.apply(this, arguments);
        }
    },
});

core.action_registry.add('plaid_online_sync_widget', PlaidAccountConfigurationWidget);
core.action_registry.add('plaid_online_sync_end_widget', PlaidAccountEndResult);

});
odoo.define('web_studio.WebClient', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var WebClient = require('web.WebClient');

var SystrayItem = require('web_studio.SystrayItem');
var bus = require('web_studio.bus');

var _t = core._t;

if (!session.is_admin) {
    // Studio is only available for the Administrator, so display a notification
    // if another user tries to access it through the url
    WebClient.include({
        show_application: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var qs = $.deparam.querystring();
                if (qs.studio !== undefined) {
                    self.notification_manager.notify(_t("Access error"), _t("Studio is only available for the Administrator"), true);
                    // Remove studio from the url, without reloading
                    delete qs.studio;
                    var l = window.location;
                    var url = l.protocol + "//" + l.host + l.pathname + '?' + $.param(qs) + l.hash;
                    window.history.pushState({ path:url }, '', url);
                }
            });
        },
    });

    return;
}

WebClient.include({
    custom_events: _.extend({}, WebClient.prototype.custom_events, {
        'click_studio_mode': 'toggle_studio_mode',
        'new_app_created': 'on_new_app_created',
        'reload_menu_data': 'on_reload_menu_data',
    }),

    init: function() {
        this._super.apply(this, arguments);
        this.studio_on = false;
        this.studio_info_def = null;

        bus.on('studio_toggled', this, function (mode) {
            this.studio_on = !!mode;
            this.update_context(!!mode);
            this.$el.toggleClass('o_in_studio', !!mode);
        });
    },

    on_new_app_created: function(ev) {
        var self = this;

        this.toggle_studio_mode().then(function() {
            self.instanciate_menu_widgets().then(function() {
                self.on_app_clicked({data: {menu_id: ev.data.menu_id, action_id: ev.data.action_id}});
                self.menu.toggle_mode(false);  // display app switcher button
           });
        });
    },

    on_reload_menu_data: function(ev) {
        var self = this;

        var current_primary_menu = this.menu.current_primary_menu;

        var action = this.edited_action;
        var action_desc = action && action.action_descr || null;
        var active_view = action && action.get_active_view();
        var mode = this.studio_on && (this.app_switcher_displayed ? 'app_creator' : 'main');
        return $.when(mode && this.load_studio_info()).then(function(studio_info) {
            return self.instanciate_menu_widgets().then(function() {
                // reload previous state
                self.menu.toggle_mode(self.app_switcher_displayed);
                self.menu.change_menu_section(current_primary_menu); // entering the current menu
                if (self.app_switcher_displayed) {
                    self.append_app_switcher();
                }

                self.menu.switch_studio_mode(mode, studio_info, action_desc, active_view);
                self._update_studio_systray(self.studio_on);
                self.app_switcher.toggle_studio_mode(self.studio_on);

                if (ev && ev.data.keep_open) {
                    self.menu.edit_menu.on_click(new Event('click'));
                }
                if (ev && ev.data.def) {
                    ev.data.def.resolve();
                }
            });
        });
    },

    // Performs the initial RPC for studio to get the global useful information for Studio
    load_studio_info: function() {
        if (!this.studio_info_def) {
            this.studio_info_def = session.rpc('/web_studio/init');
        }
        return this.studio_info_def;
    },

    toggle_studio_mode: function() {
        this.studio_on = !this.studio_on;
        var self = this;
        var action = this.action_manager.get_inner_action();
        var action_desc = action && action.action_descr || null;
        var active_view = action && action.get_active_view();
        var mode = this.studio_on && (this.app_switcher_displayed ? 'app_creator' : 'main');

        this.update_context(!!mode);

        var defs = [];
        if (this.studio_on) {
            defs.push(this.load_studio_info());
            if (!this.app_switcher_displayed) {
                defs.push(this.open_studio('main', { action: action}));
            }
        } else if (!this.app_switcher_displayed) {
            var def = $.Deferred();
            defs.push(def);
            this.close_studio().always(def.resolve.bind(def));
        }
        return $.when.apply($, defs).then(function (studio_info) {
            bus.trigger('studio_toggled', mode, studio_info, action_desc, active_view);
            if (self.studio_on) {
                self._update_studio_systray(true);
            }
            if (!self.studio_on && self.app_switcher_displayed) {
                self.trigger_up('show_app_switcher');
            }
        });
    },

    show_application: function () {
        var self = this;
        var _super = this._super.bind(this, arguments);
        var qs = $.deparam.querystring();
        var studio_mode = _.contains(['main', 'app_creator'], qs.studio) ? qs.studio : false;
        if (!studio_mode) {
            return this._super.apply(this, arguments);
        }
        this.update_context(true);
        return this.load_studio_info().then(function(studio_info) {
            return _super().then(function () {
                var action_descr;
                var def;
                if (studio_mode === 'main') {
                    var action = self.action_manager.get_inner_action();
                    if (action) {
                        action_descr = action.action_descr;
                        def = self.open_studio('main', { action: action });
                    } else {
                        return $.when();
                    }
                }
                return $.when(def).then(function () {
                    bus.trigger('studio_toggled', studio_mode, studio_info, action_descr);
                });
            });
        });
    },

    open_studio: function (mode, options) {
        options = options || {};
        var self = this;
        var action = options.action;
        var action_options = {};
        var def;
        // Stash current action stack to restore it when leaving studio
        this.action_manager.stash_action_stack();
        this.studio_on = true;
        this.edited_action = action;
        if (action) {
            // we are editing an action, not in app creator mode
            var index = action.widget.dataset.index;
            this.studio_ids = action.widget.dataset.ids;
            this.studio_id = index ? this.studio_ids[index] : (this.studio_ids[0] || false);
            action_options.active_view = action.get_active_view();
            action_options.action = action.action_descr;
            def = session.rpc('/web_studio/chatter_allowed', {
                model: action_options.action.res_model,
            });
        }
        return $.when(def).then(function(chatter_allowed) {
            self.studio_chatter_allowed = chatter_allowed;
            // grep: action_web_studio_app_creator, action_web_studio_main
            return self.do_action('action_web_studio_' + mode, action_options);
        });
    },

    do_action: function(action, options) {
        var mode = this.studio_on && (this.app_switcher_displayed ? 'app_creator' : 'main');
        if (mode === 'main') {
            options = options || {};
            options.ids = this.studio_ids;
            options.res_id = this.studio_id;
            options.chatter_allowed = this.studio_chatter_allowed;
        }
        return this._super.apply(this, arguments);
    },

    close_studio: function () {
        this.studio_on = false;
        this.edited_action = undefined;
        return this.action_manager.restore_action_stack();
    },

    update_context: function (in_studio) {
        if (in_studio) {
            // Write in user_context that we are in Studio
            // This is used server-side to flag with Studio the ir.model.data of customizations
            session.user_context.studio = 1;
        } else {
            delete session.user_context.studio;
        }
    },

    do_push_state: function () {
        if (this.studio_on) {
            return; // keep edited action in url when we navigate in studio to allow restoring it on refresh
        }
        return this._super.apply(this, arguments);
    },

    /**
     * Studio is disabled by default in systray
     * Add conditions here to enable it
     */
    current_action_updated: function(action) {
        this._super.apply(this, arguments);
        if (this.studio_on) {
            if (action && action.action_descr.tag !== 'action_web_studio_app_creator') {
                this._update_studio_systray(true);
                return;
            }
        }
        if (action && action.action_descr.xml_id) {
            var descr = action.action_descr;
            if (descr.type === 'ir.actions.act_window' || descr.xml_id === 'action_web_studio_main') {
                this._update_studio_systray(true);
                return;
            }
        }
        this._update_studio_systray(false);
    },

    toggle_app_switcher: function(display) {
        this._super.apply(this, arguments);
        if (display) { this._update_studio_systray(true); }
    },

    _update_studio_systray: function(show) {
        var systray_item = _.find(this.menu.systray_menu.widgets, function(item) {
            return item instanceof SystrayItem;
        });
        if (show) {
           systray_item.enable();
        } else {
            systray_item.disable();
        }
    },
});

});

odoo.define('web_studio.AppSwitcher', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var web_client = require('web.web_client');
var AppSwitcher = require('web_enterprise.AppSwitcher');

var bus = require('web_studio.bus');

var QWeb = core.qweb;

if (!session.is_admin) {
    return;
}

AppSwitcher.include({
    events: _.extend(AppSwitcher.prototype.events, {
        'click .o_web_studio_new_app': function (event) {
            event.preventDefault();
            web_client.open_studio('app_creator').then(function () {
                core.bus.trigger('toggle_mode', true, false);
            });
        },
    }),
    start: function () {
        bus.on('studio_toggled', this, this.toggle_studio_mode);
        return this._super.apply(this, arguments);
    },
    toggle_studio_mode: function (display) {
        this.in_studio_mode = display;
        if (!this.in_DOM) {
            return;
        }
        if (display) {
            this.on_detach_callback();  // de-bind hanlders on appswitcher
            this.in_DOM = true;  // avoid effect of on_detach_callback
            this.to_studio_mode();
        } else {
            this.$new_app.remove();
            this.on_attach_callback();
        }
    },
    to_studio_mode: function () {
        this.state = this.get_initial_state();
        this.render();
        this.$new_app = $(QWeb.render('web_studio.AppCreator.NewApp'));
        this.$new_app.appendTo(this.$('.o_apps'));
    },
    on_menuitem_click: function (event) {
        // One cannot enter an app from the appswitcher in studio mode
        if (this.in_studio_mode) {
            event.preventDefault();
        } else {
            this._super.apply(this, arguments);
        }
    },
    on_attach_callback: function () {
        this.in_DOM = true;
        if (this.in_studio_mode) {
            this.to_studio_mode();
        } else {
            this._super.apply(this, arguments);
        }
    },
    on_detach_callback: function () {
        this._super.apply(this, arguments);
        this.in_DOM = false;
    },
});

});

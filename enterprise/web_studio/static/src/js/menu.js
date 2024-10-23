odoo.define('web_studio.Menu', function (require) {
"use strict";

var core = require('web.core');
var data_manager = require('web.data_manager');
var Menu = require('web_enterprise.Menu');
var session = require('web.session');

var bus = require('web_studio.bus');
var EditMenu = require('web_studio.EditMenu');
var SubMenu = require('web_studio.SubMenu');
var SystrayItem = require('web_studio.SystrayItem');

var qweb = core.qweb;
var _t = core._t;

Menu.include({
    events: _.extend({}, Menu.prototype.events, {
        'mouseenter .o_menu_sections > li:not(.open)': function(e) {
            if (this.studio_mode) {
                var $opened = this.$('.o_menu_sections > li.open');
                if($opened.length) {
                    $opened.removeClass('open');
                }
                $(e.currentTarget).addClass('open').find('> a').focus();
            }
        },
        'mouseleave .o_menu_sections': function() {
            if (this.studio_mode) {
                var $opened = this.$('.o_menu_sections > li.open');
                if($opened.length) {
                    $opened.removeClass('open');
                }
            }
        },
        'click .o_web_studio_export': function(event) {
            event.preventDefault();
            // Export all customizations done by Studio in a zip file containing Odoo modules
            var $export = $(event.currentTarget);
            $export.addClass('o_disabled'); // disable the export button while it is exporting
            session.get_file({
                url: '/web_studio/export',
                complete: $export.removeClass.bind($export, 'o_disabled'), // re-enable export
            });
        },
        'click .o_web_studio_import': function(event) {
            event.preventDefault();
            var self = this;
            // Open a dialog allowing to import new modules (e.g. exported customizations)
            this.do_action({
                name: 'Import modules',
                res_model: 'base.import.module',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                target: 'new',
                context: {
                    dialog_size: 'medium',
                },
            }, {
                on_close: function() {
                    data_manager.invalidate(); // invalidate cache
                    self.trigger_up('reload_menu_data'); // reload menus
                },
            });
        },
    }),

    init: function() {
        this._super.apply(this, arguments);
        bus.on('studio_toggled', this, this.switch_studio_mode.bind(this));
    },

    switch_studio_mode: function(studio_mode, studio_info, action, active_view) {
        if (this.studio_mode === studio_mode) {
            return;
        }

        var $main_navbar = this.$('.o_main_navbar');
        if (studio_mode) {
            if (!this.studio_mode) {
                this.$systray = $main_navbar
                    .find('.o_menu_systray')
                    .children(':not(".o_user_menu, .o_web_studio_navbar_item")')
                    .detach();
                this.$menu_toggle = $main_navbar.find('.o_menu_toggle').detach();
            }

            if (studio_mode === 'main') {
                // Not in app switcher
                var options = { multi_lang: studio_info.multi_lang };
                this.studio_menu = new SubMenu(this, action, active_view, options);
                this.studio_menu.insertAfter($main_navbar);

                if (this.current_primary_menu) {
                    this.edit_menu = new EditMenu(this, this.menu_data, this.current_primary_menu);
                    this.edit_menu.appendTo($main_navbar.find('.o_menu_sections'));
                }
            } else {
                // In app switcher
                this.$app_switcher_menu = $(qweb.render('web_studio.AppSwitcherMenu'));
                $main_navbar.prepend(this.$app_switcher_menu);
            }
            // Notes
            this.$notes = $('<div>')
                .addClass('o_web_studio_notes')
                .append($('<a>', {
                    href: 'http://pad.odoo.com/p/customization-' + studio_info.dbuuid,
                    target: '_blank',
                    text: _t("Notes"),
                }));
            this.$notes.insertAfter($main_navbar.find('.o_menu_systray'));
        } else {
            if (this.edit_menu) {
                this.edit_menu.destroy();
                this.edit_menu = undefined;
            }
            if (this.studio_menu) {
                this.studio_menu.destroy();
                this.studio_menu = undefined;
            }
            if (this.$notes) {
                this.$notes.remove();
                this.$nodes = undefined;
            }
            if (this.$app_switcher_menu) {
                this.$app_switcher_menu.remove();
                this.$app_switcher_menu = undefined;
            }
            if (this.studio_mode) {
                this.$systray.prependTo('.o_menu_systray');
                this.$menu_toggle.prependTo('.o_main_navbar');
            }
        }

        this.studio_mode = studio_mode;
    },

    _on_secondary_menu_click: function() {
        if (this.studio_mode) {
            var systray_item = _.find(this.systray_menu.widgets, function(item) {
                return item instanceof SystrayItem;
            });
            systray_item.bump();
        } else {
            this._super.apply(this, arguments);
        }
    },
});

});

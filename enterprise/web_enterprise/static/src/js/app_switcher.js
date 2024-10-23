odoo.define('web_enterprise.AppSwitcher', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var NBR_ICONS = 6;

function visit(tree, callback, path) {
    path = path || [];
    callback(tree, path);
    _.each(tree.children, function(node) {
        visit(node, callback, path.concat(tree));
    });
}

function is_mobile() {
    return config.device.size_class <= config.device.SIZES.XS;
}

var AppSwitcher = Widget.extend({
    template: 'AppSwitcher',
    events: {
        'input input.o_menu_search_input': function(e) {
            if(!e.target.value) {
                // on odoo [10.0,11.0] ignore IE11 placeholder input events
                if (this.state.is_searching !== true) {
                    return;
                }
                this.state = this.get_initial_state();
                this.state.is_searching = true;
            }
            this.update({search: e.target.value, focus: 0});
        },
        'click .o_menuitem': 'on_menuitem_click',
        'compositionstart': 'on_compositionstart', // [DO NOT FORWARD PORT]
        'compositionend': 'on_compositionend', // [DO NOT FORWARD PORT]
    },
    init: function (parent, menu_data) {
        this._super.apply(this, arguments);
        this.menu_data = this.process_menu_data(menu_data);
        this.state = this.get_initial_state();
    },
    start: function () {
        this.$input = this.$('input');
        this.$menu_search = this.$('.o_menu_search');
        this.$main_content = this.$('.o_application_switcher_scrollable');
        return this._super.apply(this, arguments);
    },
    get_initial_state: function () {
        return {
            apps: _.where(this.menu_data, {is_app: true}),
            menu_items: [],
            focus: null,  // index of focused element
            is_searching: is_mobile(),
            isComposing: false, // [DO NOT FORWARD PORT] composing mode for input (e.g. japanese)
        };
    },
    process_menu_data: function(menu_data) {
        var result = [];
        visit(menu_data, function (menu_item, parents) {
            if (!menu_item.id || !menu_item.action) {
                return;
            }
            var item = {
                label: _.pluck(parents.slice(1), 'name').concat(menu_item.name).join(' / '),
                id: menu_item.id,
                xmlid: menu_item.xmlid,
                action: menu_item.action ? menu_item.action.split(',')[1] : '',
                is_app: !menu_item.parent_id,
                web_icon: menu_item.web_icon,
            };
            if (!menu_item.parent_id) {
                if (menu_item.web_icon_data) {
                    item.web_icon_data = 'data:image/png;base64,' + menu_item.web_icon_data;
                } else if (item.web_icon) {
                    var icon_data = item.web_icon.split(',');
                    var $icon = $('<div>')
                        .addClass('o_app_icon')
                        .css('background-color', icon_data[2])
                        .append(
                            $('<i>')
                                .addClass(icon_data[0])
                                .css('color', icon_data[1])
                        );
                    item.web_icon = $icon[0].outerHTML;
                } else {
                    item.web_icon_data = '/web_enterprise/static/src/img/default_icon_app.png';
                }
            } else {
                item.menu_id = parents[1].id;
            }
            result.push(item);
        });
        return result;
    },
    on_attach_callback: function () {
        core.bus.on("keydown", this, this.on_keydown);
        this.state = this.get_initial_state();
        this.$input.val('');
        if (!is_mobile()) { // [DO NOT FORWARD PORT]
            this.$input.focus(); // focus on search bar at loading
        }
        this.render();
    },
    on_compositionstart: function(event) { // [DO NOT FORWARD PORT]
        this.state.isComposing = true;
    },
    on_compositionend: function(event) { // [DO NOT FORWARD PORT]
        this.state.isComposing = false;
    },
    on_detach_callback: function () {
        core.bus.off("keydown", this, this.on_keydown);
    },
    get_app_index: function () {
        return this.state.focus < this.state.apps.length ? this.state.focus : null;
    },
    get_menu_index: function () {
        var state = this.state;
        return state.focus >= state.apps.length ? state.focus - state.apps.length : null;
    },
    on_keydown: function(event) {
        var is_editable = event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA" || event.target.isContentEditable;
        if (is_editable && event.target !== this.$input[0]) {
            return;
        }
        var state = this.state;
        var elem_focused = state.focus !== null;
        var app_focused = elem_focused && state.focus < state.apps.length;
        var delta = app_focused ? NBR_ICONS : 1;
        var $input = this.$input;
        switch (event.which) {
            case $.ui.keyCode.DOWN:
                this.update({focus: elem_focused ? delta : 0});
                event.preventDefault();
                break;
            case $.ui.keyCode.RIGHT:
                if ($input.is(':focus') && $input[0].selectionEnd < $input.val().length) {
                    return;
                }
                this.update({focus: elem_focused ? 1 : 0});
                event.preventDefault();
                break;
            case $.ui.keyCode.TAB:
                if ($input.val() === "") {
                    return;
                }
                event.preventDefault();
                var f = elem_focused ? (event.shiftKey ? -1 : 1) : 0;
                this.update({focus: f});
                break;
            case $.ui.keyCode.UP:
                this.update({focus: elem_focused ? -delta : 0});
                event.preventDefault();
                break;
            case $.ui.keyCode.LEFT:
                if ($input.is(':focus') && $input[0].selectionStart > 0) {
                    return;
                }
                this.update({focus: elem_focused ? -1 : 0});
                event.preventDefault();
                break;
            case $.ui.keyCode.ENTER:
                if (elem_focused) {
                    var menus = app_focused ? state.apps : state.menu_items;
                    var index = app_focused ? state.focus : state.focus - state.apps.length;
                    this.open_menu(menus[index]);
                    event.preventDefault();
                }
                return;
            case $.ui.keyCode.PAGE_DOWN:
            case $.ui.keyCode.PAGE_UP:
            case 16: // Shift
            case 17: // CTRL
            case 18: // Alt
                break;
            case 67: // c
            case 88: // x
                // keep focus and selection on keyboard copy and cut
                if (event.ctrlKey || event.metaKey) {
                    break;
                }
            default:
                if (!this.$input.is(':focus')) {
                    this.$input.focus();
                }
        }
    },
    on_menuitem_click: function (e) {
        e.preventDefault();
        var menu_id = $(e.currentTarget).data('menu');
        this.open_menu(_.findWhere(this.menu_data, {id: menu_id}));
    },
    update: function(data) {
        var self = this;
        if (data.search) {
            var options = {extract: function(el) { return el.label; }};
            var search_results = fuzzy.filter(data.search, this.menu_data, options);
            var results = _.map(search_results, function (result) {
                return self.menu_data[result.index];
            });
            this.state = _.extend(this.state, {
                apps: _.where(results, {is_app: true}),
                menu_items: _.where(results, {is_app: false}),
                focus: results.length ? 0 : null,
                is_searching: true,
            });
        }
        if (this.state.focus !== null && 'focus' in data) {
            var state = this.state;
            var app_nbr = state.apps.length;
            var new_index = data.focus + (state.focus || 0);
            if (new_index >= app_nbr && state.focus < app_nbr && data.focus > 0) {
                if (state.focus + data.focus - (state.focus % data.focus) < app_nbr) {
                    new_index = app_nbr - 1;
                } else {
                    new_index = app_nbr;
                }
            }
            if (new_index < app_nbr && state.focus >= app_nbr && data.focus < 0) {
                new_index = app_nbr - (app_nbr % NBR_ICONS);
                if (new_index === app_nbr) {
                    new_index = app_nbr - NBR_ICONS;
                }
            }
            if (new_index < 0) {
                new_index = state.apps.length + state.menu_items.length - 1;
            }
            if (new_index >= state.apps.length + state.menu_items.length) {
                new_index = 0;
            }
            state.focus = new_index;
        }
        this.render();
    },
    render: function() {
        this.$menu_search.toggleClass('o_bar_hidden', !this.state.is_searching);
        this.$main_content.html(QWeb.render('AppSwitcher.Content', { widget: this }));
        var $focused = this.$main_content.find('.o_focused');
        if ($focused.length && !is_mobile()) {
            if (!this.state.isComposing) { // DO NOT FORWARD-PORT
                $focused.focus();
            }
            this.$el.scrollTo($focused, {offset: {top:-0.5*this.$el.height()}});
        }

        var offset = window.innerWidth - (this.$main_content.offset().left * 2 + this.$main_content.outerWidth());
        if (offset) {
            this.$el.css('padding-left', "+=" + offset);
        }
    },
    open_menu: function(menu) {
        this.trigger_up(menu.is_app ? 'app_clicked' : 'menu_clicked', {
            menu_id: menu.id,
            action_id: menu.action,
        });
        if (!menu.is_app) {
            core.bus.trigger('change_menu_section', menu.menu_id);
        }
    }
});

return AppSwitcher;

});

odoo.define('web_enterprise.ExpirationPanel', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var session = require('web.session');
var utils = require('web.utils');
var AppSwitcher = require('web_enterprise.AppSwitcher');

var QWeb = core.qweb;

AppSwitcher.include({
    events: _.extend(AppSwitcher.prototype.events, {
        'click .oe_instance_buy': 'enterprise_buy',
        'click .oe_instance_renew': 'enterprise_renew',
        'click .oe_instance_upsell': 'enterprise_upsell',
        'click a.oe_instance_register_show': function() {
            this.$('.oe_instance_register_form').slideToggle();
        },
        'click #confirm_enterprise_code': 'enterprise_code_submit',
        'click .oe_instance_hide_panel': 'enterprise_hide_panel',
        'click .check_enterprise_status': 'enterprise_check_status',
    }),
    start: function () {
        return this._super.apply(this, arguments).then(this.enterprise_expiration_check.bind(this));
    },
    /** Checks for the database expiration date and display a warning accordingly. */
    enterprise_expiration_check: function() {
        var self = this;

        // don't show the expiration warning for portal users
        if (!(session.warning))  {
            return;
        }
        var today = new moment();
        // if no date found, assume 1 month and hope for the best
        var dbexpiration_date = new moment(session.expiration_date || new moment().add(30, 'd'));
        var duration = moment.duration(dbexpiration_date.diff(today));
        var options = {
            'diffDays': Math.round(duration.asDays()),
            'dbexpiration_reason': session.expiration_reason,
            'warning': session.warning,
        };
        self.enterprise_show_panel(options);
    },
    enterprise_check_status: function(ev) {
        ev.preventDefault();
        var Publisher = new Model('publisher_warranty.contract');
        var P = new Model('ir.config_parameter');
        P.call('get_param', ['database.expiration_date']).then(function(old_date) {
            var dbexpiration_date = new moment(old_date);
            var duration = moment.duration(dbexpiration_date.diff(new moment()));
            if (Math.round(duration.asDays()) < 30) {
                Publisher.call('update_notification', [[]]).then(function() {
                    $.when(
                        P.call('get_param', ['database.expiration_date']))
                    .then(function(dbexpiration_date) {
                        $('.oe_instance_register').hide();
                        $('.database_expiration_panel .alert').removeClass('alert-info alert-warning alert-danger');
                        if (dbexpiration_date != old_date && new moment(dbexpiration_date) > new moment()) {
                            $.unblockUI();
                            $('.oe_instance_hide_panel').show();
                            $('.database_expiration_panel .alert').addClass('alert-success');
                            $('.valid_date').html(moment(dbexpiration_date).format('LL'));
                            $('.oe_subscription_updated').show();
                        } else {
                            window.location.reload();
                        }
                    });
                });
            }
        });
    },
    enterprise_show_panel: function(options) {
        //Show expiration panel 30 days before the expiry
        var self = this;
        var hide_cookie = utils.get_cookie('oe_instance_hide_panel');
        if ((options.diffDays <= 30 && !hide_cookie) || options.diffDays <= 0) {

            var expiration_panel = $(QWeb.render('WebClient.database_expiration_panel', {
                has_mail: _.includes(session.module_list, 'mail'),
                diffDays: options.diffDays,
                dbexpiration_reason:options.dbexpiration_reason,
                warning: options.warning
            })).insertBefore(self.$menu_search);

            if (options.diffDays <= 0) {
                expiration_panel.children().addClass('alert-danger');
                expiration_panel.find('.oe_instance_buy').on('click.widget_events', self.proxy('enterprise_buy'));
                expiration_panel.find('.oe_instance_renew').on('click.widget_events', self.proxy('enterprise_renew'));
                expiration_panel.find('.oe_instance_upsell').on('click.widget_events', self.proxy('enterprise_upsell'));
                expiration_panel.find('.check_enterprise_status').on('click.widget_events', self.proxy('enterprise_check_status'));
                expiration_panel.find('.oe_instance_hide_panel').hide();
                $.blockUI({message: expiration_panel.find('.database_expiration_panel')[0],
                           css: { cursor : 'auto' },
                           overlayCSS: { cursor : 'auto' } });
            }
        }
    },
    enterprise_hide_panel: function(ev) {
        ev.preventDefault();
        utils.set_cookie('oe_instance_hide_panel', true, 24*60*60);
        $('.database_expiration_panel').hide();
    },
    /** Save the registration code then triggers a ping to submit it*/
    enterprise_code_submit: function(ev) {
        ev.preventDefault();
        var enterprise_code = $('.database_expiration_panel').find('#enterprise_code').val();
        if (!enterprise_code) {
            var $c = $('#enterprise_code');
            $c.attr('placeholder', $c.attr('title')); // raise attention to input
            return;
        }
        var P = new Model('ir.config_parameter');
        var Publisher = new Model('publisher_warranty.contract');
        $.when(
            P.call('get_param', ['database.expiration_date']),
            P.call('set_param', ['database.enterprise_code', enterprise_code]))
        .then(function(old_date) {
            utils.set_cookie('oe_instance_hide_panel', '', -1);
            Publisher.call('update_notification', [[]]).then(function() {
                $.unblockUI();
                $.when(
                    P.call('get_param', ['database.expiration_date']),
                    P.call('get_param', ['database.expiration_reason']))
                .then(function(dbexpiration_date) {
                    $('.oe_instance_register').hide();
                    $('.database_expiration_panel .alert').removeClass('alert-info alert-warning alert-danger');
                    if (dbexpiration_date !== old_date) {
                        $('.oe_instance_hide_panel').show();
                        $('.database_expiration_panel .alert').addClass('alert-success');
                        $('.valid_date').html(moment(dbexpiration_date).format('LL'));
                        $('.oe_instance_success').show();
                    } else {
                        $('.database_expiration_panel .alert').addClass('alert-danger');
                        $('.oe_instance_error, .oe_instance_register_form').show();
                        $('#confirm_enterprise_code').html('Retry');
                    }
                });
            });
        });
    },
    enterprise_buy: function() {
        var limit_date = new moment().subtract(15, 'days').format("YYYY-MM-DD");
        new Model("res.users").call("search_count", [[["share", "=", false],["login_date", ">=", limit_date]]]).then(function(users) {
            window.location = $.param.querystring("https://www.odoo.com/odoo-enterprise/upgrade", {num_users: users});
        });
    },
    enterprise_renew: function() {
        var P = new Model('ir.config_parameter');
        var Publisher = new Model('publisher_warranty.contract');
        $.when(
            P.call('get_param', ['database.expiration_date']))
        .then(function(old_date) {
            utils.set_cookie('oe_instance_hide_panel', '', -1);
            Publisher.call('update_notification', [[]]).then(function() {
                $.when(
                    P.call('get_param', ['database.expiration_date']),
                    P.call('get_param', ['database.expiration_reason']),
                    P.call('get_param', ['database.enterprise_code']))
                .then(function(new_date, dbexpiration_reason, enterprise_code) {
                    var mt_new_date = new moment(new_date);
                    if (new_date != old_date && mt_new_date > new moment()) {
                        $.unblockUI();
                        $('.oe_instance_register').hide();
                        $('.database_expiration_panel .alert').removeClass('alert-info alert-warning alert-danger');
                        $('.database_expiration_panel .alert').addClass('alert-success');
                        $('.valid_date').html(moment(new_date).format('LL'));
                        $('.oe_instance_success, .oe_instance_hide_panel').show();
                    } else {
                            var params = enterprise_code ? {contract: enterprise_code} : {};
                            window.location = $.param.querystring("https://www.odoo.com/odoo-enterprise/renew", params);
                    }
                });
            });
        });
    },
    enterprise_upsell: function() {
        var limit_date = new moment().subtract(15, 'days').format("YYYY-MM-DD");
        new Model('ir.config_parameter').call('get_param', ['database.enterprise_code']).then(function(contract) {
            new Model("res.users").call("search_count", [[["share", "=", false],["login_date", ">=", limit_date]]]).then(function(users) {
                var params = contract ? {contract: contract, num_users: users} : {num_users: users};
                window.location = $.param.querystring("https://www.odoo.com/odoo-enterprise/upsell", params);
            });
        });
    },
});

});

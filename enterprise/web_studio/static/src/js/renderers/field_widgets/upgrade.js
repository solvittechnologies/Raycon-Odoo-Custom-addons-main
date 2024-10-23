odoo.define('web_studio.upgrade_widgets', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var framework = require('web.framework');
var Model = require('web.DataModel');

var _t = core._t;
var QWeb = core.qweb;

var FieldBoolean = basic_fields.FieldBoolean;
var FieldRadio = basic_fields.FieldRadio;

/**
 *  This widget is intended to be used in config settings.
 *  When checked, an upgrade popup is showed to the user.
 */
var AbstractFieldUpgrade = {
    render: function() {
        this._super.apply(this, arguments);
        this.insert_enterprise_label($("<span>", {
            text: "Enterprise",
            'class': "label label-primary oe_inline"
        }));
    },

    open_dialog: function() {
        var message = $(QWeb.render('EnterpriseUpgrade'));

        var buttons = [
            {
                text: _t("Upgrade now"),
                classes: 'btn-primary',
                close: true,
                click: this.confirm_upgrade,
            },
            {
                text: _t("Cancel"),
                close: true,
            },
        ];

        return new Dialog(this, {
            size: 'medium',
            buttons: buttons,
            $content: $('<div>', {
                html: message,
            }),
            title: _t("Odoo Enterprise"),
        }).open();
    },

    confirm_upgrade: function() {
        new Model("res.users").call("search_count", [[["share", "=", false]]]).then(function(data) {
            framework.redirect("https://www.odoo.com/odoo-enterprise/upgrade?num_users=" + data);
        });
    },

    on_click_input: function(event) {
        if ($(event.currentTarget).prop("checked")) {
            this.open_dialog().on('closed', this, this.reset_value);
        }
    },

    reset_value: function() {},
    insert_enterprise_label: function($enterprise_label) {},
};

var UpgradeBoolean = FieldBoolean.extend(AbstractFieldUpgrade, {
    events: _.extend({}, FieldBoolean.prototype.events, {
        'click input': 'on_click_input',
    }),

    insert_enterprise_label: function($enterprise_label) {
        this.$el.append('&nbsp;').append($enterprise_label);
    },
    reset_value: function() {
        this.$input.prop("checked", false).change();
    },
});

var UpgradeRadio = FieldRadio.extend(AbstractFieldUpgrade, {
    events: _.extend({}, FieldRadio.prototype.events, {
        'click input:last': 'on_click_input',
    }),

    insert_enterprise_label: function($enterprise_label) {
        this.$('label').last().append('&nbsp;').append($enterprise_label);
    },
    reset_value: function() {
        this.$('input').first().prop("checked", true).click();
    },
    is_set: function() {
        return true;
    },
});


field_registry
    .add('upgrade_boolean', UpgradeBoolean)
    .add('upgrade_radio', UpgradeRadio);

});

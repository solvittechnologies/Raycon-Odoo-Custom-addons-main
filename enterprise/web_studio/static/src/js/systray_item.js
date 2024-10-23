odoo.define('web_studio.SystrayItem', function (require) {
"use strict";

var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');


/*
 * Menu item appended in the systray part of the navbar
 * Instantiate this widget iff user is admin
 */

if (!session.is_admin) {
    return;
}

var SystrayItem = Widget.extend({
    events: {
        'click': function (event) {
            event.preventDefault();
            this.disable();
            this.trigger_up('click_studio_mode');
        },
    },
    sequence: 1, // force this item to be the first one to the left of the UserMenu in the systray
    template: 'web_studio.SystrayItem',

    init: function () {
        this._super.apply(this, arguments);
        this.disabled = true;
    },
    enable: function () {
        this.disabled = false;
        this.renderElement();
    },
    disable: function () {
        this.disabled = true;
        this.renderElement();
    },
    bump: function () {
        this.$('img').openerpBounce();
    },
});

SystrayMenu.Items.unshift(SystrayItem);

return SystrayItem;

});

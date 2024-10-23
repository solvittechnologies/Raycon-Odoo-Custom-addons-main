odoo.define('web_studio.NewElementDialog', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var _t = core._t;

var NewElementDialog = Dialog.extend({
    template: 'web_studio.NewElementDialog',
    events: {
        'click td.o_web_studio_new_element': 'add_element',
    },
    init: function(parent, node, position) {
        var options = {
            title: _t('Add an Element'),
            size: 'medium',
            buttons: [
                {text: _t("Cancel"), close: true},
            ],
        };
        this.node = node;
        this.position = position;
        this._super(parent, options);
    },
    add_element: function(event) {
        event.preventDefault();

        var self = this;
        var element = $(event.currentTarget).attr('data-element');
        this.trigger_up('view_change', {
            type: 'add',
            structure: element,
            node: this.node,
            position: this.position,
            on_success: function() {
                self.close();
            },
        });
    },
});

return NewElementDialog;

});

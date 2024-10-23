odoo.define('web_studio.phone', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var config = require('web.config');
var field_registry = require('web.field_registry');

var EmailWidget = basic_fields.EmailWidget;

var FieldPhone = EmailWidget.extend({
    prefix: 'tel',
    init: function() {
        this._super.apply(this, arguments);
        if (this.mode === 'readonly' && !this._can_call()) {
            this.tagName = 'span';
        }
    },
    render_readonly: function() {
        this._super();
        if(this._can_call()) {
            var text = this.$el.text();
            this.$el.html(text.substr(0, text.length/2) + "&shy;" + text.substr(text.length/2)); // To prevent Skype app to find the phone number
        } else {
            this.$el.removeClass('o_form_uri');
        }
    },
    _can_call: function() {
        // Phone fields are clickable in readonly on small screens ~= on phones
        // This can be overriden by call-capable modules to display a clickable
        // link in different situations, like always regardless of screen size,
        // or only allow national calls for example.
        return config.device.size_class <= config.device.SIZES.XS;
    }
});

field_registry
    .add('phone', FieldPhone);

});

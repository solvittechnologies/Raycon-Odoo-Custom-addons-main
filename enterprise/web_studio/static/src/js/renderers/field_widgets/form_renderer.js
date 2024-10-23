odoo.define('mail.form_renderer', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');

// Include the FormRenderer to hide the chatter when creating a new record
FormRenderer.include({
    _render_node: function(node) {
        if (node.tag === 'div' && node.attrs.class === 'oe_chatter' &&
            this.mode === 'edit' && !this.state.res_id) {
            return $('<div>');
        } else {
            return this._super.apply(this, arguments);
        }
    },
});

});

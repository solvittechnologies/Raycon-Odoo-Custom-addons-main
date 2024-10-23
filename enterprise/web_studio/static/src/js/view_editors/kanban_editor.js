odoo.define('web_studio.KanbanEditor', function (require) {
"use strict";

var core = require('web.core');
var KanbanRenderer = require('web.KanbanRenderer');

var _t = core._t;

return KanbanRenderer.extend({
    _render: function () {
        if (this.state.data.length === 0) {
            return this._render_empty_editor();
        }
        return this._super.apply(this, arguments);
    },
    _render_empty_editor: function() {
        var style = {
            color: 'white',
            fontSize: '24px',
        };
        var $message = $('<div>').css(style).text(_t('No records to display'));
        this.$el.html($message);
        return $.when();
    }
});

});

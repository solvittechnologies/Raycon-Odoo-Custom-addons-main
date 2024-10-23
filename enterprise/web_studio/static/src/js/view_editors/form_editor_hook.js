odoo.define('web_studio.FormEditorHook', function (require) {
"use strict";

var Widget = require('web.Widget');

var NewElementDialog = require('web_studio.NewElementDialog');

var FormEditorHook = Widget.extend({
    className: 'o_web_studio_new_line',
    events: {
        'click': 'on_click',
    },

    init: function(parent, node, position) {
        this._super.apply(this, arguments);
        this.node = node;
        this.position = position;
        if (this.node.tag === 'field' || (this.node.tag === 'group' && position === 'inside')) {
            this.tagName = 'tr';
        }
    },
    start: function() {
        var $content;
        switch (this.node.tag) {
            case 'field':
                $content = $('<td colspan="2">').append(this._render_span());
                break;
            case 'group':
                if (this.position === 'inside') {
                    $content = $('<td colspan="2">').append(this._render_span());
                } else {
                    $content = this._render_span();
                }
                break;
            case 'page':
                this.$el.css({padding: '25px'});
                $content = this._render_span();
                break;
        }
        this.$el.append($content);
        return this._super.apply(this, arguments);
    },
    _render_span: function() {
        return $('<span>').addClass('o_web_studio_new_line_separator');
    },
    on_click: function() {
        new NewElementDialog(this, this.node, this.position).open();
    },
});

return FormEditorHook;

});

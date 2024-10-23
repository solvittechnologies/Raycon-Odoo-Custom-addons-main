odoo.define('web_studio.SearchEditor', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');

return AbstractRenderer.extend({
    _render: function() {
        this.$el.empty();
        var $search_view = $('<div>').addClass('o_web_studio_no_preview').html('Preview not available yet.');
        this.$el.html($search_view);
        return this._super.apply(this, arguments);
    },
});

});

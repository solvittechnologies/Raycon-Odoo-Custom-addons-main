odoo.define('web_studio.GraphEditor', function (require) {
"use strict";

var OldViewRenderers = require('web_studio.OldViewRenderers');

return OldViewRenderers.extend({
    view_type: 'graph',
});

});

odoo.define('web_studio.ReportEditorSidebar', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

return Widget.extend({
    template: 'web_studio.ReportEditorSidebar',
    events: {
        'click .o_web_studio_xml_editor': 'on_xml_editor',
        'click .o_web_studio_parameters': 'on_parameters',
    },
    init: function() {
        this._super.apply(this, arguments);
        this.debug = core.debug;
    },
    on_parameters: function() {
        this.trigger_up('open_report_form');
    },
    on_xml_editor: function () {
        this.trigger_up('open_xml_editor');
    },
});

});

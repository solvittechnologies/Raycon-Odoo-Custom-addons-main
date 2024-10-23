odoo.define('mrp_barcode.MrpBarcodeHandler', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Dialog = require('web.Dialog');
var FormViewBarcodeHandler = require('barcodes.FormViewBarcodeHandler');

var _t = core._t;


var WorkorderBarcodeHandler = FormViewBarcodeHandler.extend({

    init: function(parent, context) {
        if (parent.ViewManager.action) {
            this.form_view_initial_mode = parent.ViewManager.action.context.form_view_initial_mode;
        } else if (parent.ViewManager.view_form) {
            this.form_view_initial_mode = parent.ViewManager.view_form.options.initial_mode;
        }
        return this._super.apply(this, arguments);
    },
    start: function() {
        this._super();
        this.MrpWorkorder = new Model("mrp.workorder");
        this.form_view.options.disable_autofocus = 'true';
        if (this.form_view_initial_mode) {
            this.form_view.options.initial_mode = this.form_view_initial_mode;
        }
    },
});


core.form_widget_registry.add('workorder_barcode_handler', WorkorderBarcodeHandler);

});

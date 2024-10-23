odoo.define('web_studio.ReportEditor', function (require) {
"use strict";

var ReportAction = require('report.client_action');
var core = require('web.core');
var customize = require('web_studio.customize');
var ReportEditorSidebar = require('web_studio.ReportEditorSidebar');
var XMLEditor = require('web_studio.XMLEditor');

var ReportEditor = ReportAction.extend({

    template: 'web_studio.report_editor',
    custom_events: {
        'open_report_form': 'open_report_form',
        'open_xml_editor': 'open_xml_editor',
        'close_xml_editor': 'close_xml_editor',
        'save_xml_editor': 'save_xml_editor',
    },

    init: function(parent, action, options) {
        options = options || {};
        options = _.extend(options, {
            report_url: '/report/html/' + action.report_name + '/' + action.active_ids,
            report_name: action.report_name,
            report_file: action.report_file,
            name: action.name,
            display_name: action.display_name,
            context: {
                active_ids: action.active_ids.split(','),
            },
        });
        this.view_id = action.view_id;
        this.res_model = 'ir.actions.report.xml';
        this.res_id = action.id;
        this._super.apply(this, arguments);
    },
    start: function() {
        var self = this;
        this.sidebar = new ReportEditorSidebar(this);

        return this._super.apply(this, arguments).then(function() {
            return self.sidebar.appendTo(self.$el);
        });
    },
    _update_control_panel_buttons: function () {
        this._super.apply(this, arguments);
        // the edit button is available in Studio even if not in debug mode
        this.$buttons.filter('div.o_edit_mode_available').toggle(this.edit_mode_available && ! this.in_edit_mode);
    },
    open_report_form: function() {
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: this.res_model,
            res_id: this.res_id,
            views: [[false, 'form']],
            target: 'current',
        });
    },
    open_xml_editor: function () {
        var self = this;

        if (!this.XMLEditor) {
            this.XMLEditor = new XMLEditor(this, this.view_id);
        }

        $.when(this.XMLEditor.appendTo(this.$el)).then(function() {
            self.sidebar.$el.detach();
            self.XMLEditor.open();
        });
    },
    close_xml_editor: function () {
        this.XMLEditor.$el.detach();
        this.sidebar.$el.appendTo(this.$el);
    },
    save_xml_editor: function (event) {
        var self = this;

        return customize.edit_view_arch(
            event.data.view_id,
            event.data.new_arch
        ).then(function() {
            // reload iframe
            self.$('iframe').attr('src', self.report_url);

            if (event.data.on_success) {
                event.data.on_success();
            }
        });
    },
});

core.action_registry.add('studio_report_editor', ReportEditor);

});

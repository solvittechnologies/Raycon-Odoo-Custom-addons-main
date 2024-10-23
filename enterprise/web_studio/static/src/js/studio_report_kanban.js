odoo.define('web_studio.studio_report_kanban', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var Model = require('web.Model');
var KanbanView = require('web_kanban.KanbanView');

var _t = core._t;

var StudioReportKanbanView = KanbanView.extend({
    open_record: function(event) {
        var self = this;
        new Model('ir.actions.report.xml').call('studio_edit', [event.data.id]).then(function(action) {
            if (action.active_ids.length) {
                self.do_action(action);
            } else {
                new Dialog(this, {
                    size: 'medium',
                    title: _t('No record to display.'),
                    $content: $('<div>', {
                        text: _t("First, quit Odoo Studio to create a new entity. Then, open Odoo Studio to create or edit reports."),
                    }),
                }).open();
            }
        });
    },
});

core.view_registry.add('studio_report_kanban', StudioReportKanbanView);

return StudioReportKanbanView;

});

odoo.define('event_barcode.EventScanView', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var Session = require('web.session');
var Notification = require('web.notification').Notification;
var NotificationManager = require('web.notification').NotificationManager;
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');
var time = require('web.time');

var QWeb = core.qweb;
var _t = core._t;

// Success Notification with thumbs-up icon
var Success = Notification.extend({
    template: 'event_barcode_success'
});

var NotificationSuccess = NotificationManager.extend({
    success: function(title, text, sticky) {
        return this.display(new Success(this, title, text, sticky));
    }
});

// load widget with main barcode scanning View
var EventScanView = Widget.extend(BarcodeHandlerMixin, {
    template: 'event_barcode_template',
    events: {
        'keypress #event_barcode': 'on_manual_scan',
        'click .o_event_social': 'open_attendees',
        'click .o_event_info': 'open_event_form',
    },

    init: function(parent, action) {
        BarcodeHandlerMixin.init.call(this, parent, action);
        this._super.apply(this, arguments);
        this.action = action;
        this.parent = parent;
    },
    willStart: function() {
        var self = this;
        return this._super().then(function() {
            return Session.rpc('/event_barcode/event', {
                event_id: self.action.context.active_id
            }).then(function(result) {
                self.data = self.prepare_data(result);
            });
        });
    },
    start: function() {
        var self = this;
        this.notification_manager = new NotificationSuccess();
        this.notification_manager.appendTo(self.parent.$el);
        this.updateCount(
            self.$('.o_event_reg_attendee'),
            self.data.count
        );
    },
    prepare_data: function(result) {
        var start_date = moment(time.auto_str_to_date(result.start_date));
        var end_date = moment(time.auto_str_to_date(result.end_date));
        var localedata = start_date.localeData();
        result['date'] =  start_date.date() === end_date.date() ? start_date.date() : _.str.sprintf("%s - %s", start_date.date(), end_date.date());
        result['month'] = start_date.month() === end_date.month() ? localedata._months[start_date.month()] : _.str.sprintf('%s - %s', localedata._monthsShort[start_date.month()], localedata._monthsShort[end_date.month()]);
        return result;
    },
    on_manual_scan: function(e) {
        if (e.which === 13) { // Enter
            var value = $(e.currentTarget).val().trim();
            if(value) {
                this.on_barcode_scanned(value);
                $(e.currentTarget).val('');
            } else {
                this.do_warn(_t('Error'), _t('Invalid user input'));
            }
        }
    },
    on_attach_callback: function() {
        this.start_listening();
    },
    on_detach_callback: function() {
        this.stop_listening();
    },
    on_barcode_scanned: function(barcode) {
        var self = this;
        Session.rpc('/event_barcode/register_attendee', {
             barcode: barcode,
             event_id: self.action.context.active_id
        }).then(function(result) {
            if (result.success) {
                self.updateCount(
                    self.$('.o_event_reg_attendee'),
                    result.count
                );
                self.notification_manager.success(result.success);
            } else if (result.warning) {
                self.do_warn(_("Warning"), result.warning);
            }
        });
    },
    open_attendees: function() {
        this.do_action({
            name: "Attendees",
            type:'ir.actions.act_window',
            res_model: 'event.registration',
            views: [[false, 'list'], [false, 'form']],
            context :{
                'search_default_event_id': this.action.context.active_id,
                'default_event_id': this.action.context.active_id,
                'search_default_expected': true
            }
        });
    },
    open_event_form: function() {
        this.do_action({
            name: 'Event',
            type: 'ir.actions.act_window',
            res_model: 'event.event',
            views: [[false, 'form'], [false, 'kanban'], [false, 'calendar'], [false, 'list']],
            res_id: this.action.context.active_id,
        });
    },
    updateCount: function(element, count) {
        element.html(count);
    }
});

core.action_registry.add('even_barcode.scan_view', EventScanView);

return {
    Success: Success,
    NotificationSuccess: NotificationSuccess,
    EventScanView: EventScanView
};

});

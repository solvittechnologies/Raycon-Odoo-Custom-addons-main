odoo.define('web_studio.FieldManagerMixin', function (require) {
"use strict";

var ViewModel = require('web.ViewModel');

return {
    custom_events: {
        field_changed: function(event) {
            this.on_field_changed(event);
        },
        name_create: function(event) {
            var data = event.data;
            if (!data.on_success) { return; }
            return this.datamodel
                .name_create(data.model, data.name)
                .then(data.on_success)
                .fail(function () {
                    if (data.on_fail) {
                        data.on_fail();
                    }
                });
        },
        name_get: function(event) {
            var data = event.data;
            if (!data.on_success) { return; }
            return this.datamodel.name_get(data.model, data.ids).then(data.on_success); // fixme: handle context
        },
        name_search: function(event) {
            var data = event.data;
            if (!data.on_success) { return; }
            return this.datamodel
                .name_search(data.model, data.search_val, data.domain, data.operator, data.limit)
                .then(data.on_success);
        },
        perform_model_rpc: function(event) {
            var data = event.data;
            return this.datamodel.perform_model_rpc(data.model, data.method, data.args, data.kwargs).then(function (result) {
                if (data.on_success) { data.on_success(result); }
            }).fail(function () {
                if (data.on_fail) { data.on_fail(); }
            });
        },
        perform_rpc: function(event) {
            var data = event.data;
            return this.datamodel.perform_rpc(data.route, data.args).then(function (result) {
                if (data.on_success) { data.on_success(result); }
            }).fail(function () {
                if (data.on_fail) { data.on_fail(); }
            });
        },
        load: function(event) {
            var self = this;
            var data = event.data;
            if (!data.on_success) { return; }
            if ('limit' in data) {
                this.datamodel.set_limit(data.id, data.limit);
            }
            if ('offset' in data) {
                this.datamodel.set_offset(data.id, data.offset);
            }
            return this.datamodel.reload(data.id).then(function(db_id) {
                data.on_success(self.datamodel.get(db_id));
            });
        },
    },
    init: function () {
        this.datamodel = new ViewModel();
    },
    on_field_changed: function(event) {
        var self = this;
        var local_id = event.data.local_id;
        var field = event.data.name;
        var value = event.data.value;
        this.datamodel.notify_change(local_id, field, value).then(function (result) {
            if (event.data.force_save) {
                self.datamodel.save(local_id).then(function () {
                    self.confirm_save(local_id);
                });
            } else {
                self.confirm_onchange(local_id, result);
            }
        });
    },
    confirm_onchange: function (id, fields) {
        // to be implemented
    },
    confirm_save: function (id) {
        // to be implemented, if necessary
    },
};

});

odoo.define('web_studio.data', function (require) {
"use strict";

var data = require('web.data');

function build_eval_context (record) {
    var field_values = _.extend({}, record.data, {
        active_model: record.model,
    });
    if ('id' in record.data) {
        field_values.active_id = record.data.id;
        field_values.active_ids = [record.data.id];
    }
    return new data.CompoundContext(field_values);
}

data.build_context = function(record, context) {
    context = context || {};
    if (record.context) {
        context = new data.CompoundContext(record.context, context);
    }
    var eval_context = build_eval_context(record);
    return new data.CompoundContext(context).set_eval_context(eval_context);
};

data.build_domain = function(record, domain) {
    domain = domain || [];
    if (record.domain) {
        domain = new data.CompoundDomain(record.domain, domain);
    }
    var eval_context = build_eval_context(record);
    return new data.CompoundDomain(domain).set_eval_context(eval_context);
};

});

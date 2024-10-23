odoo.define('web.field_utils', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var time = require('web.time');
var utils = require('web.utils');

function format_boolean(value) {
    var $input = $('<input type="checkbox">')
                .prop('checked', value)
                .prop('disabled', true);
    return $('<div>')
                .addClass('o_checkbox')
                .append($input)
                .append($('<span>'));
}

function format_char(value) {
    return value === false ? '' : value;
}

function format_date(value) {
    var l10n = core._t.database.parameters;
    var date_format = time.strftime_to_moment_format(l10n.date_format);
    return moment(time.str_to_date(value)).format(date_format);
}

function format_datetime(value) {
    var l10n = core._t.database.parameters;
    var date_format = time.strftime_to_moment_format(l10n.date_format);
    var time_format = time.strftime_to_moment_format(l10n.time_format);
    var datetime_format = date_format + ' ' + time_format;
    return moment(time.str_to_datetime(value)).format(datetime_format);
}

function format_float(value, field) {
    var l10n = core._t.database.parameters;
    var precision = field.digits ? field.digits[1] : 2;
    var formatted = _.str.sprintf('%.' + precision + 'f', value || 0).split('.');
    formatted[0] = utils.insert_thousand_seps(formatted[0]);
    return formatted.join(l10n.decimal_point);
}

function format_id(value) {
    return value.toString();
}

function format_integer(value) {
    if (!value && value !== 0) {
        return false;
    }
    return utils.insert_thousand_seps(_.str.sprintf('%d', value));
}

function format_many2one(value, field, data, options) {
    var m2o_value = _.find(options.relational_data[field.__attrs.name], function(d) {
        return d[0] === value;
    });
    return m2o_value ? m2o_value[1] : '';
}

function format_many2many(value, field, data, options) {
    var display_names = [];
    var relational_data = options.relational_data;
    var info;
    _.each(value, function(id) {
        info = _.find(relational_data[field.__attrs.name], {id: id});
        display_names.push(info.display_name);
    });
    return display_names.join(', ');
}

function format_monetary(value, field, data, options) {
    options = options || {};
    var currency_field = options.currency_field || field.currency_field || 'currency_id';
    var currency_id = data[currency_field] && data[currency_field];
    var currency = session.get_currency(currency_id);
    var digits_precision = (currency && currency.digits) || [69,2];
    var precision = digits_precision[1];
    var formatted = _.str.sprintf('%.' + precision + 'f', value || 0).split('.');
    formatted[0] = utils.insert_thousand_seps(formatted[0]);
    var l10n = core._t.database.parameters;
    var formatted_value = formatted.join(l10n.decimal_point);

    if (!currency) {
        return formatted_value;
    }
    if (currency.position === "after") {
        return formatted_value += '&nbsp;' + currency.symbol;
    } else {
        return currency.symbol + '&nbsp;' + formatted_value;
    }
}

function format_selection(value, field) {
    if (!value) {
        return '';
    }
    var val = _.find(field.selection, function(option) {
        return option[0] === value;
    });
    return val[1];
}

function parse_float(value) {
    value = value.replace(new RegExp(core._t.database.parameters.thousands_sep, "g"), '');
    value = value.replace(core._t.database.parameters.decimal_point, '.');
    var parsed = Number(value);
    if (isNaN(parsed)) {
        throw new Error(_.str.sprintf(core._t("'%s' is not a correct float"), value));
    }
    return parsed;
}

function parse_integer(value) {
    value = value.replace(new RegExp(core._t.database.parameters.thousands_sep, "g"), '');
    var parsed = Number(value);
    // do not accept not numbers or float values
    if (isNaN(parsed) || parsed % 1) {
        throw new Error(_.str.sprintf(core._t("'%s' is not a correct integer"), value));
    }
    return parsed;
}

function identity(value) {
    return value;
}

return {
    format_binary: identity, // todo
    format_boolean: format_boolean,
    format_char: format_char,
    format_date: format_date,
    format_datetime: format_datetime,
    format_float: format_float,
    format_html: identity, // todo
    format_id: format_id,
    format_integer: format_integer,
    format_many2many: format_many2many,
    format_many2one: format_many2one,
    format_monetary: format_monetary,
    format_one2many: identity, // todo
    format_reference: identity, // todo
    format_selection: format_selection,
    format_text: format_char,

    parse_binary: identity, // todo
    parse_boolean: identity, // todo
    parse_char: identity, // todo
    parse_date: identity, // todo
    parse_datetime: identity, // todo
    parse_float: parse_float,
    parse_html: identity, // todo
    parse_id: identity,
    parse_integer: parse_integer,
    parse_many2many: identity, // todo
    parse_many2one: identity,
    parse_monetary: identity, // todo
    parse_one2many: identity,
    parse_reference: identity, // todo
    parse_selection: identity, // todo
    parse_text: identity, // todo
};

});

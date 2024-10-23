odoo.define('web.ViewModel', function (require) {
"use strict";

var Class = require('web.Class');
var data = require('web.data'); // TODO: remove dependency to data.js
var pyeval = require('web.pyeval');
var session = require('web.session');
var utils = require('web.utils');
var new_utils = require('web.new_utils');


function find_direct_parent(parent, record) {
    if (parent.is_record) {
        return;
    }
    var index = _.indexOf(parent.data, record);
    if (index >= 0) {
        return parent;
    } else {
        var direct_parent;
        for (var i = 0; i < parent.data.length; i++) {
            direct_parent = find_direct_parent(parent.data[i], record);
            if (direct_parent) {
                return direct_parent;
            }
        }
    }
}

function get_value(field_name, value, fields) {
    if (field_name === "id") {
        return value;
    }
    if (fields[field_name].type === 'many2one') {
        return _.isArray(value) ? value[0] : value;
    }
    return value;
}

function serialize_sort(order_by) {
    return _.map(order_by, function(order) {
        return order.asc ? order.name + ' ASC' : order.name + ' DESC';
    }).join(', ');
}

var x2many_commands = {
    // (0, _, {values})
    CREATE: 0,
    create: function (values) {
        return [x2many_commands.CREATE, false, values];
    },
    // (1, id, {values})
    UPDATE: 1,
    update: function (id, values) {
        return [x2many_commands.UPDATE, id, values];
    },
    // (2, id[, _])
    DELETE: 2,
    delete: function (id) {
        return [x2many_commands.DELETE, id, false];
    },
    // (3, id[, _]) removes relation, but not linked record itself
    FORGET: 3,
    forget: function (id) {
        return [x2many_commands.FORGET, id, false];
    },
    // (4, id[, _])
    LINK_TO: 4,
    link_to: function (id) {
        return [x2many_commands.LINK_TO, id, false];
    },
    // (5[, _[, _]])
    DELETE_ALL: 5,
    delete_all: function () {
        return [5, false, false];
    },
    // (6, _, ids) replaces all linked records with provided ids
    REPLACE_WITH: 6,
    replace_with: function (ids) {
        return [6, false, ids];
    }
};

var Model = Class.extend({
    init: function() {
        this.local_data = Object.create(null);

        // this mutex is necessary to make sure some operations are done
        // sequentially, for example, an onchange needs to be completed before a
        // save is performed.
        this.mutex = new utils.Mutex();
    },
    // synchronous method, it assumes that the resource has already been loaded.
    get: function(id) {
        var element = $.extend(true, {}, this.local_data[id]);
        if (element.is_record) {
            _.extend(element.data, element.changes.data);
            _.extend(element.relational_data, element.changes.relational_data);
            delete element.changes;
        }
        return element;
    },
    // all rpcs to fetch data should go through this method
    // this will make testing easier
    perform_rpc: function(route, args) {
        return session.rpc(route, args);
    },
    perform_model_rpc: function(model, method, args, kwargs) {
        return this.perform_rpc('/web/dataset/call_kw/' + model + '/' + method, {
            model: model,
            method: method,
            args: args || [],
            kwargs: kwargs || {},
        });
    },
    make_record: function(model, fields) {
        var record_fields = {};
        var data = {};
        var relational_data = {};
        _.each(fields, function (field) {
            record_fields[field.name] = _.extend({__attrs: {}}, _.pick(field, 'type', 'relation', 'domain'));
            if (field.value) {
                data[field.name] = field.value;
                if (field.relational_value) {
                    relational_data[field.name] = field.relational_value;
                }
            }
        });
        var record = this._make_record(model, {
            data: data,
            fields: record_fields,
            relational_data: relational_data,
        });
        return record.id;
    },
    // load takes a model and some informations (such ad id, or domain)
    // it should return a deferred which resolves to the desired data,
    // also, it should register the data in the local_data, with all the
    // parameters necessary to relaod it.
    load: function(model, params) {
        var self = this;
        var fields = params.fields;
        var def;
        _.each(fields, function(field) {
            if (field.__attrs && field.__attrs.options) {
                var options = pyeval.py_eval(field.__attrs.options || '{}');
                if (options.always_reload) {
                    field.__always_reload = true;
                }
            }
        });
        if ('id' in params && 'fields' in params) {
            if (params.id) {
                var record = this._make_record(model, params);
                def = this._fetch_record(record);
            } else {
                def = this.make_record_with_defaults(model, params.fields, params.context).then(function (id) {
                    return self.local_data[id];
                });
            }
        }
        if ('domain' in params && 'fields' in params) {
            var list = this._make_list(model, params);
            if (list.grouped_by.length) {
                def = this._fetch_grouped_list(list);
            } else {
                def = this._fetch_ungrouped_list(list);
            }
        }
        return def.then(function(result) {
                return self._fetch_relational_data(result);
            }).then(function(result) {
            return result.id;
        });
    },
    // with a valid id key from the local_data, this method is supposed to reload
    // all dirty information.
    reload: function(id) {
        var self = this;
        var element = this.local_data[id];
        var def = $.Deferred();
        if (element.is_list) {
            if (!element.grouped_by.length) {
                def = this._fetch_ungrouped_list(element);
            } else {
                def = this._fetch_grouped_list(element);
            }
        } else {
            def = this._fetch_record(element);
        }
        return def.then(function(result) {
            return self._fetch_relational_data(result);
        }).then(function(result) {
            return result.id;
        });
    },
    load_more: function(list_id) {
        var self = this;
        var list = this.local_data[list_id];
        list.offset = list.offset + list.limit;
        return this._fetch_ungrouped_list(list, {load_more: true}).then(function(result) {
            return self._fetch_relational_data(result);
        }).then(function(result) {
            return result.id;
        });
    },
    discard_changes: function(id) {
        var element = this.local_data[id];
        element.changes = {
            data: {},
            relational_data: {},
        };
        return element.id;
    },
    save: function(record_id) {
        var self = this;
        return this.mutex.exec(function () {
            var record = self.local_data[record_id];
            var method = record.res_id ? 'write' : 'create';
            var changes = record.changes.data;
            if (method === 'create') {
                _.each(record.fields, function(value, key) {
                    changes[key] = changes[key] || record.data[key];
                });
            }
            // replace changes in x2many fields by the appropriate commands
            var commands = self._generate_x2many_commands(record.fields, record.data, record.changes);
            _.extend(record.changes.data, commands);
            // FIXME: don't do RPC if there is no change to save
            var args = method === 'write' ? [[record.data.id], changes] : [changes];
            return self.perform_model_rpc(record.model, method, args, {
                context: session.user_context, // todo: combine with view context
            }).then(function(id) {
                if (method === 'create') {
                    record.res_id = id;  // create returns an id, write returns a boolean
                }
                self.discard_changes(record_id);
                return self._fetch_record(record);
            }).then(function() {
                return self._fetch_relational_data(record);
            });
        });
    },
    toggle_active: function (record_ids, value, parent_id) {
        var self = this;
        return this.mutex.exec(function () {
            var list = self.local_data[parent_id];
            var records = _.map(record_ids, function (id) { return self.local_data[id]; });
            return self.perform_model_rpc(list.model, 'write', [_.pluck(records, 'res_id'), {active: value}], {
                context: session.user_context, // todo: combine with view context
            }).then(self._fetch_ungrouped_list.bind(self, list)).then(function(result) {
                return self._fetch_relational_data(result);
            }).then(function(result) {
                return result.id;
            });
        });
    },
    _generate_x2many_commands: function(fields, data, changes) {
        var commands = {};
        _.each(changes.data, function(value, field) {
            if (fields[field].type === 'many2many') {
                commands[field] = [x2many_commands.replace_with(value)]; // FIXME: be smarter?
            } else if (fields[field].type === 'one2many') {
                var removed_ids = _.difference(data[field], value);
                var created_ids = _.difference(value, data[field]);
                commands[field] = [];
                _.each(removed_ids, function(id) {
                    commands[field].push(x2many_commands.delete(id));
                });
                _.each(created_ids, function(id) {
                    var record = _.find(changes.relational_data[field].data, {res_id: id});
                    commands[field].push(x2many_commands.create(_.omit(record.data, 'id')));
                });
            }
        });
        return commands;
    },
    _make_record: function(model, params) {
        var data = params.data || {};
        var record = {
            id: _.uniqueId(),
            res_id: params.id || data.id,
            model: model,
            fields: params.fields,
            data: data,
            is_record: true,
            context: params.context,
            relational_data: params.relational_data || {},
            changes: {
                data: {},
                relational_data: {},
            },
        };
        this.local_data[record.id] = record;
        return record;
    },
    _make_list: function(model, params) {
        var list = {
            id: _.uniqueId(),
            model: model,
            fields: params.fields,
            grouped_by: params.grouped_by || [],
            ordered_by: params.ordered_by || [],
            offset: 0,
            count: params.count || 0,
            data: [],
            limit: params.limit || 80,
            is_list: true,
            domain: params.domain,
            context: params.context,
            res_ids: params.res_ids,
            cache: {},
            open_group_by_default: params.open_group_by_default,
            relational_data: params.relational_data || {},
        };
        this.local_data[list.id] = list;
        return list;
    },
    _make_group: function(model, params) {
        var value_is_array = params.value instanceof Array;
        return _.extend(this._make_list(model, params), {
            is_open: false,
            is_group: true,
            res_id: value_is_array ? params.value[0] : undefined,
            value: value_is_array ? params.value[1] : params.value,
            aggregate_values: params.aggregate_values || {},
        });
    },
    notify_change: function(record_id, field_name, value) {
        var self = this;
        var record = this.local_data[record_id];
        var field = record.fields[field_name];
        var fields_changed = [];
        var changes = record.changes;
        var def;
        if (field.type === 'one2many' || field.type === 'many2many') {
            fields_changed.push(field_name);
            var list = changes.relational_data[field_name];
            if (!list) {
                list = this.get(record.relational_data[field_name].id);
                changes.relational_data[field_name] = list;
            }
            if (field.type === 'one2many') {
                changes.data[field_name] = changes.data[field_name] || record.data[field_name].slice(0);
                if (value[0] === 'CREATE') {
                    var view = field.views.tree || field.views.kanban;
                    var data = value[1];
                    data.id = _.uniqueId('virtual_id_');
                    var subrecord = this._make_record(field.relation, {
                        data: data,
                        fields: view.fields,
                    });
                    changes.data[field_name] = changes.data[field_name].concat(subrecord.res_id);
                    list.cache[record.res_id] = subrecord;
                    if (list.data.length < list.limit) {
                        list.data.push(subrecord);
                    }
                    list.count++;
                } else if (value[0] === 'DELETE') {
                    changes.data[field_name].splice(_.indexOf(changes.data[field_name], value[1]), 1);
                    var record_index = _.indexOf(list.data, _.findWhere(list.data, {res_id: value[1]}));
                    if (record_index > -1) {
                        list.data.splice(record_index, 1);
                    }
                    delete list.cache[record.res_id];
                    list.count--;
                }
            } else {
                changes.data[field_name] = value;
                list.res_ids = value;
                list.count = list.res_ids.length;
                def = this._fetch_ungrouped_list(list).then(this._fetch_relational_data.bind(this));
            }
        } else {
            changes.data[field_name] = value;
        }
        return $.when(def).then(function() {
            if (field.__attrs.on_change) {
                return self._apply_on_change(record, [field_name]).then(function(result) {
                    return fields_changed.concat(Object.keys(result && result.value || {}));
                });
            }
            return $.when(fields_changed);
        });
    },
    _apply_on_change: function(record, fields) {
        var self = this;
        var onchange_spec = this._build_onchange_specs(record.fields);
        var id_list = record.data.id ? [record.data.id] : [];
        var context = data.build_context(record, session.user_context).eval();
        return this.mutex.exec(function() {
            // replace changes in x2many fields by the appropriate commands
            var commands = self._generate_x2many_commands(record.fields, record.data, record.changes);
            var changed_data = _.extend({id: false}, record.data, record.changes.data, commands);
            var args = [id_list, changed_data, fields, onchange_spec, context];
            return self.perform_model_rpc(record.model, 'onchange', args, {}).then(function(result) {
                var defs = [];
                _.each(result.value, function(val, name) {
                    var field = record.fields[name];
                    if (!field) { return; } // ignore changes of unknown fields
                    if (field.type === 'one2many') {
                        var fields;
                        if ('tree' in field.views) {
                            fields = field.views.tree.fields;
                        } else {
                            fields = field.views.kanban.fields;
                        }
                        var data = self._make_list(field.relation, {
                            fields: fields
                        });
                        data.data = _.map(val.slice(1), function(elem) {
                            var record = self._make_record(field.relation, {data: elem[2], fields: fields});
                            return record;
                        });
                        defs.push(self._fetch_relational_data(data));
                        data.count = val.length - 1;
                        record.changes.relational_data[name] = data;
                        record.changes.data[name] = [false, false];
                    } else if (field.type === 'many2one') {
                        record.changes.data[name] = val[0];

                        // aab, is this ok?
                        if (!record.changes.relational_data[name]) {
                            record.changes.relational_data[name] = [];
                        }
                        
                        record.changes.relational_data[name].push(val);
                    } else {
                        record.changes.data[name] = val;
                    }
                });
                return $.when.apply($, defs).then(function () {
                    return result;
                });
            });
        });
    },
    _build_onchange_specs: function(fields) {
        // TODO: replace this function by some generic tree function in utils

        var onchange_specs = {};
        _.each(fields, function(field, name) {
            onchange_specs[name] = (field.__attrs && field.__attrs.on_change) || "";
            _.each(field.views, function(view) {
                _.each(view.fields, function(field, subname) {
                    onchange_specs[name + '.' + subname] = (field.__attrs && field.__attrs.on_change) || "";
                });
            });
        });
        return onchange_specs;
    },
    set_sort: function(list_id, field_name) {
        var list = this.local_data[list_id];
        if (list.is_record) {
            return;
        }
        list.offset = 0;
        if (list.ordered_by.length === 0) {
            list.ordered_by.push({name: field_name, asc: true});
        } else if (list.ordered_by[0].name === field_name){
            list.ordered_by[0].asc = !list.ordered_by[0].asc;
        } else {
            var ordered_by = _.reject(list.ordered_by, function (o) {
                return o.name === field_name;
            });
            list.ordered_by = [{name: field_name, asc: true}].concat(ordered_by);
        }
        return this;
    },
    set_domain: function(list_id, domain) {
        var list = this.local_data[list_id];
        list.domain = domain;
        return this;
    },
    set_context: function(id, context) {
        var element = this.local_data[id];
        element.context = context;
        return this;
    },
    set_group_by: function(list_id, group_by) {
        var list = this.local_data[list_id];
        list.grouped_by = group_by;
        return this;
    },
    set_offset: function(list_id, offset) {
        var list = this.local_data[list_id];
        list.offset = offset;
        return this;
    },
    set_limit: function(list_id, limit) {
        var list = this.local_data[list_id];
        list.limit = limit;
        return this;
    },
    is_dirty: function(id) {
        return !_.isEmpty(this.local_data[id].changes);
    },
    get_context: function(context) {
        var ctx = new data.CompoundContext(session.user_context, context);
        try {
            pyeval.ensure_evaluated([], {context: ctx});
        } catch(e) {
            ctx = session.user_context;
        }
        return ctx;
    },
    _fetch_record: function(record) {
        var self = this;
        if (!('__last_update' in record.fields)) {
            record.fields.__last_update = {};
        }
        return this.perform_model_rpc(record.model, 'read', [record.res_id, Object.keys(record.fields)], {
            context: { 'bin_size': true },
        }).then(function(result) {
            result = result[0];
            record.data = result;
            return self._postprocess(record);
        });
    },
    _postprocess: function(record) {
        var self = this;
        var defs = [];
        _.each(record.fields, function(field, name) {
            if (field.__fetch_status && !field.__status_information) {
                var field_values = _.mapObject(record.data, function (val, key) {
                    return get_value(key, val, record.fields);
                });
                var _domain = new data.CompoundDomain(field.domain).set_eval_context(field_values);
                var domain = pyeval.eval('domain', _domain);
                var fold_field = pyeval.py_eval(field.__attrs.options || '{}').fold_field;
                var fetch_status_information = self.perform_rpc('/web/dataset/search_read', {
                    model: field.relation,
                    fields: [fold_field],
                    domain: domain,
                }).then(function(result) {
                    var ids = _.map(result.records, function(r) { return r.id; });
                    return self.name_get(field.relation, ids, {
                        context: self.get_context(field.__attrs.context)
                    }).then(function(name_gets) {
                        _.each(result.records, function(record) {
                            var name_get = _.find(name_gets, function(n) {
                                return n[0] === record.id;
                            });
                            record.display_name = name_get[1];
                        });
                        field.__status_information = result.records;
                    });
                });
                defs.push(fetch_status_information);
            }
            if (field.__always_reload) {
                defs.push(self.perform_model_rpc(field.relation, 'name_get', [record.data[name][0]], {
                    context: self.get_context(field.__attrs.context),
                }).then(function(result) {
                    record.data[name] = result[0];
                }));
            }
        });
        return $.when.apply($, defs).then(function () {
            return record;
        });
    },
    _fetch_ungrouped_list: function(list, options) {
        if (list.res_ids) {
            return this._read_ungrouped_list(list);
        } else {
            return this._search_read_ungrouped_list(list, options);
        }
    },
    _read_ungrouped_list: function(list) {
        var self = this;
        var def;
        var ids = [];
        var missing_ids = [];
        var upper_bound = Math.min(list.offset + list.limit, list.count);
        for (var i = list.offset; i < upper_bound; i++) {
            var id = list.res_ids[i];
            ids.push(id);
            if (!list.cache[id]) {
                missing_ids.push(id);
            }
        }
        if (missing_ids.length) {
            def = this.perform_model_rpc(list.model, 'read', [missing_ids, Object.keys(list.fields)], {
                context: {}, // FIXME
            });
        }
        return $.when(def).then(function(records) {
            list.data = [];
            _.each(ids, function(id) {
                var record = list.cache[id] || self._make_record(list.model, {
                    data: _.findWhere(records, {id: id}),
                    fields: list.fields,
                    relational_data: list.relational_data,
                });
                list.data.push(record);
                list.cache[id] = record;
            });
            return list;
        });
    },
    _search_read_ungrouped_list: function(list, options) {
        var self = this;
        options = options || {};
        return this.perform_rpc('/web/dataset/search_read', {
            model: list.model,
            fields: Object.keys(list.fields),
            domain: list.domain || [],
            offset: list.offset,
            limit: list.limit,
            sort: serialize_sort(list.ordered_by),
        }).then(function(result) {
            list.count = result.length;
            var data = _.map(result.records, function(record) {
                return self._make_record(list.model, {
                    data: record,
                    fields: list.fields,
                    relational_data: list.relational_data,
                });
            });
            if (list.data && options.load_more) {
                list.data = list.data.concat(data);
            } else {
                list.data = data;
            }
            return list;
        });
    },
    _fetch_grouped_list: function(list) {
        var self = this;
        var fields = _.uniq(Object.keys(list.fields).concat(list.grouped_by));
        return this.perform_model_rpc(list.model, 'read_group', [], {
            fields: fields,
            context: session.user_context, // todo: combine with view context
            groupby: list.grouped_by,
            domain: list.domain,
            orderby: false,
        }).then(function(groups) {
            var raw_groupby = list.grouped_by[0].split(':')[0];
            var previous_groups = _.where(list.data, {is_group:true});
            list.data = [];
            list.count = groups.length;
            var defs = [];

            _.each(groups, function(group) {
                var aggregate_values = {};
                _.each(group, function (value, key) {
                    if (_.contains(fields, key) && key !== list.grouped_by[0]) {
                        aggregate_values[key] = value;
                    }
                });
                var new_group = self._make_group(list.model, {
                    count: group[raw_groupby + '_count'],
                    domain: group.__domain,
                    fields: list.fields,
                    value: group[raw_groupby],
                    aggregate_values: aggregate_values,
                    grouped_by: list.grouped_by,
                    ordered_by: list.ordered_by,
                    limit: list.limit,
                    open_group_by_default: list.open_group_by_default,
                    relational_data: list.relational_data,
                });
                list.data.push(new_group);
                var old_group = _.find(previous_groups, function(g) {
                    return g.res_id === new_group.res_id && g.value === new_group.value;
                });
                if (old_group) {
                    new_group.is_open = old_group.is_open;
                } else {
                    new_group.is_open = '__fold' in group ? !group.__fold : new_group.open_group_by_default;
                }
                if (new_group.is_open && new_group.count > 0) {
                    defs.push(self._fetch_ungrouped_list(new_group));
                }
            });
            return $.when.apply($, defs).then(function() {
                return list;
            });
        });
    },
    _fetch_relational_data: function(element) {
        var self = this;
        var defs = [];
        _.each(element.fields, function(field, name) {
            if (field.type === 'many2one') {
                defs.push(self._fetch_many2one(element, name));
            }
            if (field.__fetch_selection && !field.__selection_information) {
                var fetch_selection_information = self.name_search(field.relation, '').then(function (result) { // fixme: handle domain and context
                    field.__selection_information = result;
                });
                defs.push(fetch_selection_information);
            } else if (field.__fetch_many2manys) {
                var fetch_many2manys = self.perform_model_rpc(field.relation, 'search', [field.domain], {
                    context: self.get_context(field.__attrs.context),
                }).then(function (record_ids) {
                    return self.name_get(field.relation, record_ids , self.get_context(field.__attrs.context));
                }).then(function(res) {
                    field.__many2manys_information = res;
                });
                defs.push(fetch_many2manys);
            } else if (field.type === 'many2many' || field.type === 'one2many') {
                defs.push(self._fetch_x2many(element, name));
            }
        });
        return $.when.apply($, defs).then(function() {
            return element;
        });
    },
    _fetch_many2one: function(element, name) {
        var name_get_ids = [];
        element.relational_data[name] = element.relational_data[name] || [];
        new_utils.traverse_records(element, function(d) {
            var value = d.data[name];
            var is_array = _.isArray(value);
            if (value) {
                var already_in_data = _.find(element.relational_data[name], function (d) {
                    return is_array ? d[0] === value[0] : d[0] === value;
                });
                if (is_array) {
                    if (!already_in_data) {
                        element.relational_data[name].push(value);
                    }
                    d.data[name] = value[0]; // id as value
                } else if (!already_in_data) {
                    name_get_ids.push(value); // default_get only returns the id
                }
            }
        });
        if (name_get_ids.length) {
            var field = element.fields[name];
            return this.perform_model_rpc(field.relation, 'name_get', [name_get_ids], {
                context: this.get_context(field.__attrs.context),
            }).then(function(name_gets) {
                element.relational_data[name] = element.relational_data[name].concat(name_gets);
            });
        }
        return $.when();
    },
    _fetch_x2many: function(element, name) {
        var field = element.fields[name];
        var ids = [];
        new_utils.traverse_records(element, function(d) {
            if (d.data[name]) {
                ids = ids.concat(d.data[name]);
            }
        });
        var view = field.views && (field.views.tree || field.views.kanban);
        if (view) {
            var list = this._make_list(field.relation, {
                res_ids: ids,
                count: ids.length,
                fields: view.fields,
                limit: 40,
            });
            element.relational_data[name] = list;
            return this._fetch_ungrouped_list(list).then(this._fetch_relational_data.bind(this));
        }
        if (field.type === 'many2many') {
            element.relational_data[name] = element.relational_data[name] || [];
            ids = _.difference(ids, _.pluck(element.relational_data[name], 'id'));
            if (ids.length) {
                var args = [_.uniq(ids), ['color', 'display_name']];
                return this.perform_model_rpc(field.relation, 'read', args, {
                    context: session.user_context,
                }).then(function (result) {
                    element.relational_data[name] = element.relational_data[name].concat(result);
                });
            }
        }
        return $.when();
    },
    toggle_group: function(group_id) {
        var self = this;
        var group = this.local_data[group_id];
        if (group.is_open) {
            group.is_open = false;
            group.data = [];
            group.offset = 0;
            return $.when(group_id);
        }
        if (!group.is_open) {
            group.is_open = true;
            return this._fetch_ungrouped_list(group).then(function(result) {
                return self._fetch_relational_data(result);
            }).then(function(result) {
                return result.id;
            });
        }
    },
    name_create: function(model, name, context) {  // fixme: move to kanban_view?
        return this.perform_model_rpc(model, 'name_create', [name], {
            context: _.extend({}, session.user_context, context),
        });
    },
    name_get: function(model, ids, context) {
        return this.perform_model_rpc(model, 'name_get', [ids], {context: context});
    },
    name_search: function (model, name, domain, operator, limit) {
        return this.perform_model_rpc(model, 'name_search', [], {
            name: name || '',
            args: domain || [],
            operator: operator || 'ilike',
            limit: limit || 0,
        });
        // fixme: correctly handle context
    },
    add_record_in_group: function (group_id, res_id) {
        var group = this.local_data[group_id];
        var new_record = this._make_record(group.model, {id: res_id, fields: group.fields});
        group.data.unshift(new_record);
        group.count++;
        return this._fetch_record(new_record)
            .then(this._fetch_relational_data.bind(this))
            .then(function(result) {
                return result.id;
            });
    },
    delete_records: function (record_ids, model, parent_id) {
        var self = this;
        var records = _.map(record_ids, function (id) { return self.local_data[id]; });
        return this.perform_model_rpc(model, 'unlink', [_.pluck(records, 'res_id')], {
            context: session.user_context, // todo: combine with view context
        }).then(function () {
            if (parent_id) {
                var parent = self.local_data[parent_id];
                _.each(records, function (record) {
                    var direct_parent = find_direct_parent(parent, record);
                    var index = _.indexOf(direct_parent.data, record);
                    direct_parent.count--;
                    direct_parent.data.splice(index, 1);
                });

                return parent.id;
            }
        });
    },
    create_group: function(name, parent_id) {
        var self = this;
        var parent = this.local_data[parent_id];
        var group_by = parent.grouped_by[0];
        var group_by_field = parent.fields[group_by];
        if (!group_by_field || group_by_field.type !== 'many2one') {
            return $.Deferred().reject(); // only supported when grouped on m2o
        }
        return this.perform_model_rpc(group_by_field.relation, 'create', [{name: name}], {
            context: session.user_context, // todo: combine with view context
        }).then(function(id) {
            var new_group = self._make_group(parent.model, {
                context: parent.context,
                domain: parent.domain.concat([[group_by,"=",id]]),
                fields: parent.fields,
                grouped_by: parent.grouped_by,
                open_group_by_default: true,
                ordered_by: parent.ordered_by,
                value: [id, name],
            });
            new_group.is_open = true;
            parent.data.push(new_group);
            parent.count++;
            return new_group.id;
        });
    },
    move_record: function(record_id, group_id, parent_id) {
        var parent = this.local_data[parent_id];
        var new_group = this.local_data[group_id];
        var values = {};
        values[parent.grouped_by[0]] = new_group.res_id || new_group.value;
        return this.save(record_id, values).then(function (result) {
            // Remove record from its current group
            for (var i = 0; i < parent.count; i++) {
                var group = parent.data[i];
                var index = _.findIndex(group.data, {id: record_id});
                if (index >= 0) {
                    group.data.splice(index, 1);
                    group.count--;
                    break;
                }
            }
            // Add record to its new group
            new_group.data.push(result);
            new_group.count++;
            return new_group.id;
        });
    },
    resequence: function(model, res_ids, parent_id) {
        if ((res_ids.length <= 1) || !model) {
            return;
        }
        var self = this;
        return this.perform_rpc('/web/dataset/resequence', {
            model: model,
            ids: res_ids,
            // fixme: correctly handle context
        }).then(function (result) {
            if (!result) {
                console.warn('Resequence could not be complete. ' +
                    'Maybe the model does not have a "sequence" field?');
            } else {
                var data = self.local_data[parent_id];
                data.data = _.sortBy(data.data, function (d) {
                    return _.indexOf(res_ids, d.res_id);
                });
            }
            return parent_id;
        });
    },
    make_record_with_defaults: function(model, fields, context) {
        var self = this;
        var fields_key = Object.keys(fields);
        fields_key = _.without(fields_key, '__last_update');

        return this.perform_model_rpc(model, 'default_get', [fields_key], {
            context: this.get_context(context),
        }).then(function (result) {
            var data = {};
            var record = self._make_record(model, {data: data, fields: fields, context: context});
            var defs = [];
            _.each(fields, function(value, key) {
                if (key in result) {
                    if (value.type === 'many2many') {
                        // We do not process default m2m values in Studio
                        // as it could be a list of commands for example, which
                        // is out of scope for this very basic implementation.
                        // Not needed in 11.0 as model.js has been rewritten.
                        data[key] = [];
                    } else {
                        data[key] = result[key];
                    }
                } else {
                    if (value.type === 'many2many') {
                        data[key] = [];
                    } else if (value.type === 'monetary') {
                        data[key] = 0;
                    } else {
                        data[key] = false;
                    }
                }
            });
            return $.when.apply($, defs)
                .then(self._postprocess.bind(self, record))
                .then(self._fetch_relational_data.bind(self, record))
                .then(self._apply_on_change.bind(self, record, fields_key))
                .then(function() {
                    return record.id;
                });
        });
    },
    duplicate_record: function (record_id, context) {
        var self = this;
        var record = this.local_data[record_id];
        return this.perform_model_rpc(record.model, 'copy', [record.data.id], {
            context: this.get_context(context),
        }).then(function(res_id) {
            return self.load(record.model, {id: res_id, fields: record.fields});
        });
    },
});

return Model;

});



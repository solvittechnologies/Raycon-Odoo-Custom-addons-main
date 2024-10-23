odoo.define('web.BasicListRenderer', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var session = require('web.session');
var core = require('web.core');
var field_utils = require('web.field_utils');
var utils = require('web.new_utils');

var _t = core._t;

// Allowed decoration on the list's rows: bold, italic and bootstrap semantics classes
var DECORATIONS = [
    'decoration-bf',
    'decoration-it',
    'decoration-danger',
    'decoration-info',
    'decoration-muted',
    'decoration-primary',
    'decoration-success',
    'decoration-warning'
];

var FIELD_CLASSES = {
    'monetary': 'o_list_number',
    'text': 'o_list_text',
    'float': 'o_list_number',
};

function make_tag(tag, content) {
    tag = '<' + tag + '>';
    return function() {
        return $(tag).html(content);
    };
}

function format_value(value, field) {
    if (field && field.type === 'selection') {
        var choice = _.find(field.selection, function(c) {return c[0] === value;});
        return choice[1];
    }
    return value || _t('Undefined');
}

return AbstractRenderer.extend({
    className: 'table-responsive',
    
    events: {
        'click .o_group_header': function(event) {
            var group = $(event.currentTarget).data('group');
            if (group.count) {
                this.trigger_up('toggle_group', {group: group});
            }
        },
        'click thead th.o_column_sortable': function(event) {
            var name = $(event.currentTarget).data('name');
            this.trigger_up('toggle_column_order', {id: this.state.id, name: name});
        },
        'click tbody .o_list_record_selector': function(event) {
            event.stopPropagation();
            this._update_selection();
            if (!$(event.currentTarget).find('input').prop('checked')) {
                this.$('thead .o_list_record_selector input').prop('checked', false);
            }
        },
        'click thead .o_list_record_selector input': function(event) {
            var checked = $(event.currentTarget).prop('checked') || false;
            this.$('tbody .o_list_record_selector input').prop('checked', checked);
            this._update_selection();
        },
    },
    init: function(parent, arch, fields, state, widgets_registry, options) {
        options = options || {};
        this._super(parent, arch, fields, state, widgets_registry);
        this.columns = _.reject(this.arch.children, function(c) {
            if (c.attrs.invisible === '1') {
                return true;
            }
            var modifiers = JSON.parse(c.attrs.modifiers || '{}');
            if (modifiers.tree_invisible) {
                return true;
            }
            return false;
        });
        this.row_decorations = _.chain(this.arch.attrs)
            .pick(function(value, key) {
                return DECORATIONS.indexOf(key) >= 0;
            }).mapObject(function(value) {
                return py.parse(py.tokenize(value));
            }).value();
        this.has_selectors = options.has_selectors;
        this.relational_data = this.state.relational_data;
        this.selection = options.selection || [];
    },
    update: function (data, selection, relational_data) {
        this.selection = selection || [];
        this.relational_data = relational_data;
        return this._super(data);
    },
    _render: function() {
        var self = this;
        var $table = $('<table>').addClass('o_list_view table table-condensed table-striped');
        this.$el.empty().append($table);
        var is_grouped = !!this.state.grouped_by.length;
        this._compute_aggregates();
        $table.toggleClass('o_list_view_grouped', is_grouped);
        $table.toggleClass('o_list_view_ungrouped', !is_grouped);
        if (is_grouped) {
            $table
                .append(this._render_header(true))
                .append(this._render_groups())
                .append(this._render_footer(true));
        } else {
            $table
                .append(this._render_header())
                .append(this._render_body())
                .append(this._render_footer());
        }
        if (this.selection.length) {
            var $checked_rows = this.$('tr').filter(function (index, el) {
                return _.contains(self.selection, $(el).data('id'));
            });
            $checked_rows.find('.o_list_record_selector input').prop('checked', true);
        }
        return this._super();
    },
    _render_selector: function(tag) {
        var $content = $('<div class="o_checkbox"><input type="checkbox"><span/></div>');
        return $('<' + tag + ' width="1">')
                    .addClass('o_list_record_selector')
                    .append($content);
    },
    _render_header: function(is_grouped) {
        var $tr = $('<tr>')
                .append(_.map(this.columns, this._render_header_cell.bind(this)));
        if (this.has_selectors) {
            $tr.prepend(this._render_selector('th'));
        }
        if (is_grouped) {
            $tr.prepend($('<th>').html('&nbsp;'));
        }
        return $('<thead>').append($tr);
    },
    _render_header_cell: function(node) {
        var order = this.state.ordered_by;
        var field = this.fields[node.attrs.name];
        var $th = $('<th>');
        if (!field) {
            return $th;
        }
        var description;
        if (node.attrs.widget) {
            var Widget = this.widgets_registry.get(node.attrs.widget);
            description = Widget && Widget.prototype.description;
        }
        if (description === undefined) {
            description = node.attrs.string || field.string;
        }
        $th
            .text(description)
            .data('name', node.attrs.name)
            .toggleClass('o-sort-down', order[0] ? order[0].name === node.attrs.name && !order[0].asc : false)
            .toggleClass('o-sort-up', order[0] ? order[0].name === node.attrs.name && order[0].asc : false)
            .addClass(this.fields[node.attrs.name].sortable && 'o_column_sortable');

        if (core.debug) {
            var field_descr = {
                field: field,
                name: node.attrs.name,
                string: description || node.attrs.name,
                record: this.state,
            };
            this.add_field_tooltip(field_descr, $th);
        }
        return $th;
    },
    _render_body: function() {
        var $rows = _.map(this.state.data, this._render_row.bind(this));
        while ($rows.length < 4) {
            $rows.push(this._render_empty_row());
        }
        return $('<tbody>').append($rows);
    },
    _render_empty_row: function() {
        var $tds = _.map(this.columns, make_tag('td', '&nbsp;'));
        if (this.has_selectors) {
            $tds.push($('<td>&nbsp;</td>'));
        }
        return $('<tr>').append($tds);
    },
    _render_row: function(record) {
        var decorations = this._compute_decorations_classnames(record);
        var $cells = _.map(this.columns, this._render_body_cell.bind(this, record));
        var $tr = $('<tr>')
                    .data('id', record.id)
                    .addClass(decorations.length && decorations.join(' '))
                    .append($cells);
        if (this.has_selectors) {
            $tr.prepend(this._render_selector('td'));
        }
        return $tr;
    },
    _render_body_cell: function(record, node) {
        var $td = $('<td>');
        if (node.tag === 'button') {
            var self = this;
            $td.addClass('o_list_button');
            var $button = $('<button type="button">').addClass('o_icon_button');
            $button.append($('<i>').addClass('fa').addClass(node.attrs.icon))
                .prop('title', node.attrs.string)
                .click(function() {
                    self.trigger_up('call_button', {attrs: node.attrs, record: record});
                });
            $td.append($button);
            return $td;
        }
        var field = this.fields[node.attrs.name];
        var value = record.data[node.attrs.name];
        if (node.attrs.widget) {
            var widgetKeys = ['list.' + node.attrs.widget, node.attrs.widget];
            var Widget = this.widgets_registry.get_any(widgetKeys);
            if (Widget) {
                var widget = new Widget(this, node.attrs.name, record, {
                    mode: 'readonly',
                });
                widget.appendTo($td);
                return $td;
            }
        }
        $td.addClass(FIELD_CLASSES[field.type]);
        var formatted_value = field_utils['format_' + field.type](value, field, record.data, {
            relational_data: this.relational_data,
        });
        return $td.html(formatted_value);
    },
    _render_footer: function(is_grouped) {
        var aggregate_values = {};
        _.each(this.columns, function (column) {
            if ('aggregate_value' in column) {
                aggregate_values[column.attrs.name] = column.aggregate_value;
            }
        });
        var $cells = this._render_aggregate_cells(aggregate_values);
        if (is_grouped) {
            $cells.unshift($('<td>'));
        }
        if (this.has_selectors) {
            $cells.unshift($('<td>'));
        }
        return $('<tfoot>').append($('<tr>').append($cells));
    },
    _compute_decorations_classnames: function(record) {
        var context = _.extend({}, record.data, {
            uid: session.uid,
            current_date: moment().format('YYYY-MM-DD')
            // TODO: time, datetime, relativedelta
        });
        return _.chain(this.row_decorations)
            .pick(function(expr) {
                return py.PY_isTrue(py.evaluate(expr, context));
            }).map(function(expr, decoration) {
                return decoration.replace('decoration', 'text');
            }).value();
    },
     _compute_aggregates: function() {
        var self = this;
        var data = [];
        if (this.selection.length) {
            utils.traverse_records(this.state, function (record) {
                if (_.contains(self.selection, record.id)) {
                    data.push(record); // find selected records
                }
            });
        } else {
            data = this.state.data;
        }
        if (data.length === 0) {
            return;
        }

        _.each(this.columns, function (column) {
            var field = self.fields[column.attrs.name];
            if (!field) {
                return;
            }
            var type = field.type;
            if (type !== 'integer' && type !== 'float' && type !== 'monetary') {
                return;
            }
            var func = column.attrs.group_operator || 'sum';
            var label = column.attrs[func];
            if (label) {
                var name = column.attrs.name;
                var count = 0;

                if (func === 'max') {
                    column.aggregate_value = -Infinity;
                } else if (func === 'min') {
                    column.aggregate_value = Infinity;
                } else {
                    column.aggregate_value = 0;
                }
                _.each(data, function (d) {
                    count += 1;
                    var value = d.is_record ? d.data[name] : d.aggregate_values[name];
                    if (func === 'avg') {
                        column.aggregate_value += value;
                    } else if (func === 'sum') {
                        column.aggregate_value += value;
                    } else if (func === 'max') {
                        column.aggregate_value = Math.max(column.aggregate_value, value);
                    } else if (func === 'min') {
                        column.aggregate_value = Math.min(column.aggregate_value, value);
                    }
                });
                if (func === 'avg') {
                    column.aggregate_value = column.aggregate_value / count;
                }
            }
        });
    },
    _render_groups: function() {
        var self = this;
        var result = [];
        var $tbody = $('<tbody>');
        _.each(this.state.data, function(group) {
            if (!$tbody) {
                $tbody = $('<tbody>');
            }
            $tbody.append(self._render_group(group));
            if (group.data.length) {
                result.push($tbody);
                var $records = _.map(group.data, function(record) {
                    return self._render_row(record).prepend($('<td>'));
                });
                result.push($('<tbody>').append($records));
                $tbody = null;
            }
        });
        if ($tbody) {
            result.push($tbody);
        }
        return result;
    },
    _render_group: function(group) {
        var $cells = this._render_aggregate_cells(group.aggregate_values);
        if (this.has_selectors) {
            $cells.unshift($('<td>'));
        }
        var field = this.fields[group.grouped_by[0]];
        var name = format_value(group.value, field);
        var $th = $('<th>')
                    .addClass('o_group_name')
                    .text(name + ' (' + group.count + ')');
        if (group.count > 0) {
            var $arrow = $('<span style="padding-right: 5px;">')
                            .addClass('fa')
                            .toggleClass('fa-caret-right', !group.is_open)
                            .toggleClass('fa-caret-down', group.is_open);
            $th.prepend($arrow);
        }
        return $('<tr>')
                    .addClass('o_group_header')
                    .data('group', group)
                    .append($th)
                    .append($cells);
    },
    _render_aggregate_cells: function (aggregate_values) {
        var self = this;
        return _.map(this.columns, function(column) {
            var $cell = $('<td>');
            if (column.attrs.name in aggregate_values) {
                var field = self.fields[column.attrs.name];
                var value = aggregate_values[column.attrs.name];
                var formatted_value = field_utils['format_' + field.type](value, field, {});
                $cell.addClass('o_list_number').html(formatted_value);
            }
            return $cell;
        });
    },
    _update_selection: function () {
        var $selected_rows = this.$('tbody .o_list_record_selector input:checked').closest('tr');
        this.selection = _.map($selected_rows, function (row) { return $(row).data('id'); });
        this.trigger_up('selection_changed', { selection: this.selection });
        this._compute_aggregates();
        this.$('tfoot').replaceWith(this._render_footer(!!this.state.grouped_by.length));
    },
});

});


odoo.define('web.ReadonlyListRenderer', function (require) {
"use strict";

var BasicListRenderer = require('web.BasicListRenderer');

return BasicListRenderer.extend({
    events: _.extend({}, BasicListRenderer.prototype.events, {
        'click tbody tr': function(event) {
            var id = $(event.currentTarget).data('id');
            if (id) {
                this.trigger_up('open_record', {id:id});
            }
        },
    }),
});

});

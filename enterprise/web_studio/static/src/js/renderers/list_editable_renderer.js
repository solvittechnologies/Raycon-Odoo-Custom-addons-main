odoo.define('web.EditableListRenderer', function (require) {
"use strict";

var BasicListRenderer = require('web.BasicListRenderer');
var core = require('web.core');

return BasicListRenderer.extend({
    custom_events: {
        field_changed: function(event) {
            event.stopped = false;
            // _.extend(this.changes, event.data);
            // this.changes.__record_id = event.data.__record_id;
            // this.changes[event.data.name] = event.data.value;
            // var record = _.findWhere(this.state.data, {id: event.data.__record_id});
            // record.data[event.data.name] = event.data.value;
            var $td = event.target.$el.parent();
            $td.addClass('o_field_dirty');
            this.current_field = event.data.name;
            this.current_value = event.data.value;
        },
        move_down: function() {
            if (this.current_row < this.state.data.length - 1) {
                this.select_cell(this.current_row + 1, this.current_col);
            }
        },
        move_up: function() {
            if (this.current_row > 0) {
                this.select_cell(this.current_row - 1, this.current_col);
            }
        },
        move_left: function() {
            if (this.current_col > 0) {
                this.select_cell(this.current_row, this.current_col - 1);
            }
        },
        move_right: function() {
            if (this.current_col < this.columns.length - 1) {
                this.select_cell(this.current_row, this.current_col + 1);
            }
        },
        move_next: function() {
            if (this.current_col < this.columns.length - 1) {
                this.select_cell(this.current_row, this.current_col + 1);
            } else if (this.current_row < this.state.data.length - 1) {
                this.select_cell(this.current_row + 1, 0);
            }
        },
        move_next_line: function() {
            if (this.current_row < this.state.data.length - 1) {
                this.select_cell(this.current_row + 1, 0);
            }
        },
    },
    events: _.extend({}, BasicListRenderer.prototype.events, {
        'click tbody td': function(event) {
            var $td = $(event.currentTarget);
            var row_index = $td.parent().data('index');
            var col_index = $td.data('index');
            if (col_index !== undefined && row_index !== undefined) {
                this.select_cell(row_index, col_index);
                event.stopPropagation();
            }
            if (this.state.grouped_by.length) {
                var id = $td.parent().data('id');
                if (id) {
                    this.trigger_up('record_selected', {id:id});
                }
            }
        },
    }),
    init: function() {
        this.current_row = null;
        this.current_col = null;
        this.current_field = null;
        this.current_value = null;
        this.changes = {};
        return this._super.apply(this, arguments);
    },
    start: function() {
        core.bus.on('click', this, function(event) {
            var $view = $(event.target).closest('table.o_list_view');
            if ($view[0] !== this.$el[0]) {
                this.unselect_row();
            }
        });
        return this._super();
    },
    _render_row: function(record, index) {
        var $row = this._super(record);
        return $row.data('index', index);
    },
    _render_body_cell: function(record, node, index) {
        var $cell = this._super(record, node);
        var field = this.fields[node.attrs.name];
        if (field.required) {
            $cell.addClass('o_required_field');
        }
        if (field.readonly) {
            $cell.addClass('o_readonly');
        }
        return $cell.data('index', index);
    },
    select_cell: function(row_index, col_index) {
        var self = this;

        // do nothing if user tries to select current cell
        if (row_index === this.current_row && col_index === this.current_col) {
            return;
        }

        // make sure the col_index is on an editable field. otherwise, find
        // next editable field, or do nothing if no such field exists
        var col_attrs, is_readonly, modifiers;
        for (; col_index < this.columns.length; col_index++) {
            col_attrs = this.columns[col_index].attrs;
            modifiers = JSON.parse(col_attrs.modifiers);
            is_readonly = modifiers.readonly;
            if (!is_readonly) {
                break;
            }
        }
        if (is_readonly) {
            return;
        }

        // if we are just changing active cell in the same row, activate the
        // corresponding widget and return
        if (row_index === this.current_row && col_index !== this.current_col) {
            var w = _.findWhere(this.widgets, {__row_index: row_index, __col_index: col_index});
            this.current_col = col_index;
            w.activate();
            return;
        }

        // if this is a different column, then we need to prepare for it by
        // unselecting the current row.  This will trigger the save, if dirty.
        if (row_index !== this.current_row) {
            this.unselect_row();
        }

        // instantiate column widgets
        var record = this.state.data[row_index];
        var $row = this.$('tbody tr').eq(row_index);
        $row.addClass('o_selected_row');

        _.each(this.columns, function(node, index) {
            var field = self.fields[node.attrs.name];
            var modifiers = JSON.parse(field.__attrs.modifiers);
            if (modifiers.readonly) {
                return;
            }

            var Widget = self.widgets_registry.get(field.type);
            var widget = new Widget(self, node.attrs.name, record, {
                mode: 'edit'
            });
            var $td = $row.find('td').eq(index + 1);
            if (widget.replace_element) {
                $td.empty();
            }
            $td.addClass('o_edit_mode');
            widget.appendTo($td);
            widget.__row_index = row_index;
            widget.__col_index = index;
            self.widgets.push(widget);
            if (index === col_index) {
                widget.activate();
            }
        });
        this.current_row = row_index;
        this.current_col = col_index;
    },
    unselect_row: function() {
        var self = this;
        if (this.current_row === null) {
            return;
        }
        var widgets = _.where(this.widgets, {__row_index: this.current_row});
        _.each(widgets, function(widget) {
            self.set_cell_value(self.current_row, widget.__col_index, true);
            widget.destroy();
            self.widgets = _.without(self.widgets, widget);
        });
        var $row = this.$('tbody tr').eq(this.current_row);
        $row.removeClass('o_selected_row');
        $row.find('td').removeClass('o_edit_mode');
        this.current_row = null;

        this.trigger_up('flush_changes');

        if ('__record_id' in this.changes) {
            this.trigger_up('record_changed', this.changes);
            this.changes = {};
        }
    },
    // notify_field_change: function() {
    //     if (this.current_field) {
    //         var record = _.findWhere(this.state.data, {id: this.changes.__record_id});
    //         this.trigger_up('field_change', {
    //             id: this.changes.__record_id,
    //             name: this.current_field,
    //             data: record.data,
    //         });
    //         this.current_field = null;
    //         this.current_value = null;
    //     }
    // },
    set_cell_value: function(row_index, col_index, keep_dirty_flag) {
        var record = this.state.data[row_index];
        var node = this.columns[col_index];
        var $td = this.$('tbody tr').eq(row_index).find('td').eq(col_index + 1);
        var $new_td = this._render_body_cell(record, node, col_index);
        if (keep_dirty_flag && $td.hasClass('o_field_dirty')) {
            $new_td.addClass('o_field_dirty');
        }
        $td.replaceWith($new_td);
    },
    confirm_save: function(record) {
        var index = _.findIndex(this.state.data, function(r) {
            return r.id === record.id;
        });
        this.state.data[index] = record;
        for (var j = 0; j < this.columns.length; j++) {
            this.set_cell_value(index, j, false);
        }
    },
    confirm_onchange: function(id, values) {
        var self = this;
        var index = _.findIndex(this.state.data, function(r) {
            return r.id === id;
        });
        _.each(values, function (val, key) {
            self.state.data[index].data[key] = val;
        });
        for (var j = 0; j < this.columns.length; j++) {
            this.set_cell_value(index, j, true);
        }
    }
});

});

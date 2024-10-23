odoo.define('web_studio.ListEditor', function (require) {
"use strict";

var ListRenderer = require('web.BasicListRenderer');

return ListRenderer.extend({
    className: ListRenderer.prototype.className + ' o_web_studio_list_view_editor',
    events: _.extend({}, ListRenderer.prototype.events, {
        'click .o_web_studio_new_column': 'on_new_column',
        'click th:not(.o_web_studio_new_column), td:not(.o_web_studio_new_column)': 'on_existing_column',
    }),

    init: function(parent, arch, fields, state, widgets_registry, options) {
        this._super.apply(this, arguments);
        if (options && options.show_invisible) {
            this.invisible_columns = _.difference(this.arch.children, this.columns);
            this.columns = this.arch.children;
        } else {
            this.invisible_columns = [];
        }
    },

    _render: function() {
        var self = this;
        var def = this._super.apply(this, arguments);

        // HOVER
        this.$('th, td').hover(function(ev) {
            var $el = $(ev.currentTarget);

            self._reset_hovered_style();

            // add style on hovered column
            $el.closest('table')
                .find('tr')
                .children(':nth-child(' + ($el.index() + 1) + ')')
                .addClass('o_hover');

            // show "+" on th
            $el.closest('table')
                .find('th')
                .eq($el.index())
                .filter('.o_web_studio_new_column')
                .find('i')
                .css('visibility', 'visible');
        });
        this.$('table').mouseleave(function() {
            self._reset_hovered_style();
        });

        // CLICK
        this.$('th, td').click(function(ev) {
            self._reset_clicked_style();

            var $el = $(ev.currentTarget);

            $el.closest('table')
                .find('th')
                .eq($el.index())
                .addClass('o_clicked');
            $el.closest('table')
                .find('tr')
                .children(':nth-child(' + ($el.index() + 1) + ')')
                .addClass('o_clicked');
        });

        return def;
    },

    _render_header: function() {
        var $header = this._super.apply(this, arguments);

        // Insert a hook after each th
        _.each($header.find('th'), function(th) {
            var $new_th = $('<th>')
                .addClass('o_web_studio_new_column')
                .append(
                    $('<i>').addClass('fa fa-plus')
            );
            $new_th.insertAfter($(th));

        });

        // Insert a hook before the first column
        var $new_th_before = $('<th>')
            .addClass('o_web_studio_new_column')
            .data('position', 'before')
            .append(
                $('<i>').addClass('fa fa-plus')
        );
        $new_th_before.prependTo($header.find('tr'));

        return $header;
    },

    _render_header_cell: function(node) {
        var $th = this._super.apply(this, arguments);
        if (_.contains(this.invisible_columns, node)) {
            $th.addClass('o_web_studio_show_invisible');
        }
        return $th;
    },

    _render_empty_row: function() {
        var $row = this._super.apply(this, arguments);

        // Inser a hook after each td
        _.each($row.find('td'), function(td) {
            $('<td>')
                .addClass('o_web_studio_new_column')
                .insertAfter($(td));
        });

        // Insert a hook before the first column
        $('<td>')
            .addClass('o_web_studio_new_column')
            .prependTo($row);

        return $row;
    },

    _render_row: function() {
        var $row = this._super.apply(this, arguments);

        // Inser a hook after each td
        _.each($row.find('td'), function(td) {
            $('<td>')
                .addClass('o_web_studio_new_column')
                .insertAfter($(td));
        });

        // Insert a hook before the first column
        $('<td>')
            .addClass('o_web_studio_new_column')
            .prependTo($row);

        return $row;
    },

    _render_footer: function() {
        var $footer = this._super.apply(this, arguments);

        // Insert a hook after each td
        _.each($footer.find('td'), function(td) {
            $('<td>')
                .addClass('o_web_studio_new_column')
                .insertAfter($(td));
        });

        // Insert a hook before the first column
        $('<td>')
            .addClass('o_web_studio_new_column')
            .prependTo($footer.find('tr'));

        return $footer;

    },

    _reset_clicked_style: function() {
        this.$('.o_clicked').removeClass('o_clicked');
    },

    _reset_hovered_style: function() {
        this.$('.o_hover').removeClass('o_hover');
        this.$('th.o_web_studio_new_column i').css('visibility', 'hidden');
    },

    on_existing_column: function(ev) {
        var $el = $(ev.currentTarget);
        var field_name = $el.closest('table').find('th').eq($el.index()).data('name');
        var node = _.find(this.columns, function (column) {
            return column.attrs.name === field_name;
        });
        this.trigger_up('field_clicked', {node: node});
    },

    on_new_column: function(ev) {
        var self = this;
        var $el = $(ev.currentTarget);

        // The information (position & field name) is on the corresponding th of the clicked element.
        var position = $el.closest('table').find('th').eq($el.index()).data('position') || 'after';
        var hooked_field_index = position === 'before' && $el.index() + 1 || $el.index() - 1;
        var field_name = $el.closest('table').find('th').eq(hooked_field_index).data('name');
        var node = _.find(this.columns, function (column) {
            return column.attrs.name === field_name;
        });

        // When there is no column in the list view, the only possible hook is inside <tree>
        if (!this.columns.length) {
            node = {
               tag: 'tree',
           };
           position = 'inside';
        }
        self.trigger_up('view_change', {
            type: 'add',
            structure: 'field',
            position: position,
            node: node,
        });
    },

});

});

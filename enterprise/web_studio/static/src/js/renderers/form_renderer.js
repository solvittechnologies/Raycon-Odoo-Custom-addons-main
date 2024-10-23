odoo.define('web.FormRenderer', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var config = require('web.config');
var core = require('web.core');
var data = require('web.data');

var _t = core._t;

var FIELD_CLASSES = {
    'one2many': 'o_field_one2many',
};

return AbstractRenderer.extend({
    className: "o_form_view",
    custom_events: _.extend({}, AbstractRenderer.prototype.custom_events, {
        update_field: function(event) {
            var field_widget = _.find(this.widgets, {name: event.data.name});
            if (field_widget) {
                field_widget.reinitialize(event.data.value);
            }
        },
    }),
    init: function(parent, arch, fields, state, widgets_registry, options) {
        this._super.apply(this, arguments);
        options = options || {};
        this.mode = options.mode || "readonly";
        this.field_values = this._get_field_values(state.data);
        this.ids_for_labels = {};
        this.view_is_editable = options.view_is_editable;
        this.has_sheet = false;
        // The rendering of some elements depends on the window's size (e.g.
        // button box), so re-render the form when the size changes
        core.bus.on('size_class', this, this._render.bind(this));
    },
    update: function(state, options) {
        this.mode = options.mode;
        this.field_values = this._get_field_values(state.data);
        this.ids_for_labels = {};
        this._super(state);
    },
    update_widgets: function(fields, state) {
        this.state = state;
        _.each(this.widgets, function (widget) {
            if (_.contains(fields, widget.name)) {
                widget.reset(state);
            }
        });
    },
    check_invalid_fields: function() {
        var invalid_fields = [];
        _.each(this.widgets, function(widget) {
            var is_valid = widget.is_valid();
            if (!is_valid) {
                invalid_fields.push(widget.name);
            }
            widget.$el.toggleClass('o_form_invalid', !is_valid);
        });
        return invalid_fields;
    },
    // return active tab pages for each notebook
    get_local_state: function() {
        var state = {};
        this.$('div.o_notebook').each(function() {
            var $notebook = $(this);
            var name = $notebook.data('name');
            var index = -1;
            $notebook.find('li').each(function (i) {
                if ($(this).hasClass('active')) {
                    index = i;
                }
            });
            state[name] = index;
        });
        return state;
    },
    // restore active tab pages for each notebook
    set_local_state: function(state) {
        this.$('div.o_notebook').each(function() {
            var $notebook = $(this);
            var name = $notebook.data('name');
            if (name in state) {
                $notebook.find('> ul > li > a[data-toggle="tab"]').eq(state[name]).click();
            }
        });
    },
    _render: function() {
        var self = this;
        this.$el.empty();
        var $form = this._render_node(this.arch).addClass(this.className);
        this.$el.html($form.contents());
        this.$el.toggleClass('o_form_nosheet', !this.has_sheet);
        this.$el.toggleClass('o_form_editable', this.mode === 'edit');
        this.$el.toggleClass('o_form_readonly', this.mode === 'readonly');
        // Attach the tooltips on the fields' label
        _.each(this.widgets, function (widget) {
            if (core.debug || widget.field.__attrs.help || widget.field.help) {
                var id_for_label = self.ids_for_labels[widget.name];
                var $label = id_for_label ? self.$('label[for=' + id_for_label + ']') : $();
                self.add_field_tooltip(widget, $label);
            }
        });
        return this._super.apply(this, arguments);
    },
    _render_node: function(node) {
        var renderer = this['_render_tag_' + node.tag];
        if (renderer) {
            return renderer.call(this, node);
        }
        if (node.tag === 'div' && node.attrs.name === 'button_box') {
            return this._render_button_box(node);
        }
        if (_.isString(node)) {
            return node;
        }
        return this._render_generic_tag(node);
    },
    _render_tag_form: function(node) {
        var $result = $('<div/>');
        if (node.attrs.class) {
            $result.addClass(node.attrs.class);
        }
        $result.append(_.map(node.children, this._render_node.bind(this)));
        return $result;
    },
    _render_tag_header: function(node) {
        var self = this;
        var $statusbar = $('<div>').addClass('o_form_statusbar');
        var $buttons = $('<div>').addClass('o_statusbar_buttons');
        $statusbar.append($buttons);
        _.each(node.children, function(child) {
            if (child.tag === 'button') {
                $buttons.append(self._render_header_button(child));
            }
            if (child.tag === 'field') {
                var widget = self._render_field_widget(child);
                $statusbar.append(widget.$el);
            }
        });
        return $statusbar;
    },
    _render_header_button: function(node) {
        var $button = $('<button>')
                        .text(node.attrs.string)
                        .addClass('btn btn-sm btn-default');
        this._add_on_click_action($button, node);
        this._handle_attributes($button, node);
        return $button;
    },
    _render_tag_sheet: function(node) {
        this.has_sheet = true;
        var $result = $('<div>').addClass('o_form_sheet_bg');
        var $sheet = $('<div>').addClass('o_form_sheet');
        $sheet.append(_.map(node.children, this._render_node.bind(this)));
        $result.append($sheet);
        return $result;
    },
    _render_generic_tag: function(node) {
        var $result = $('<' + node.tag + '>');
        _.each(node.attrs, function(attr, name) {
            if (name !== 'class' && name !== 'modifiers') {
                $result.attr(name, attr);
            }
        });
        this._handle_attributes($result, node);
        $result.append(_.map(node.children, this._render_node.bind(this)));
        return $result;
    },
    _render_tag_label: function(node) {
        var text;
        if ('string' in node.attrs) { // allow empty string
            text = node.attrs.string;
        } else if (node.attrs.for && this.fields[node.attrs.for]) {
            text = this.fields[node.attrs.for].string;
        } else  {
            return this._render_generic_tag(node);
        }
        var $result = $('<label>')
                        .addClass('o_form_label')
                        .attr('for', this._get_id_for_label(node.attrs.for))
                        .text(text);
        this._handle_attributes($result, node);
        return $result;
    },
    _render_tag_field: function (node) {
        return this._render_field_widget(node).$el;
    },
    _render_field_widget: function(node) {
        var name = node.attrs.name;
        var field = this.fields[name];
        var widget_keys = (node.attrs.widget ? ['form.' + node.attrs.widget, node.attrs.widget] : []).concat(['form.' + field.type, field.type]);
        var Widget = this.widgets_registry.get_any(widget_keys);

        if (node.attrs.widget && !this.widgets_registry.contains(node.attrs.widget)) {
            console.warn('missing widget: ' + node.attrs.widget + ' for field', name, 'of type', field.type);
        }

        var modifiers = JSON.parse(node.attrs.modifiers || "{}");
        var is_readonly = data.compute_domain(modifiers.readonly, this.field_values);
        var is_required = field.required || data.compute_domain(modifiers.required, this.field_values);
        var options = {
            view_is_editable: this.view_is_editable,
            mode: is_readonly ? 'readonly' : this.mode,
            required: is_required,
            id_for_label: this._get_id_for_label(name),
            widgets_registry: this.widgets_registry,
        };
        var widget = new Widget(this, name, this.state, options);
        this.widgets.push(widget);
        widget.__widgetRenderAndInsert(function() {});
        widget.$el.addClass(FIELD_CLASSES[field.type]);
        this._handle_attributes(widget.$el, node);

        if (is_required) {
            widget.$el.addClass('o_form_required');
        }
        if (!widget.is_set() && this.mode === 'readonly') {
            widget.$el.addClass('o_form_field_empty');
        }
        widget.$el.addClass('o_form_field');
        return widget;
    },
    _render_tag_separator: function(node) {
        return $('<div/>').addClass('o_horizontal_separator').text(node.attrs.string);
    },
    _render_tag_button: function(node) {
        var $div = $('<div>')
                        .addClass('fa fa-fw o_button_icon')
                        .addClass(node.attrs.icon);
        var $span = $('<span>').text(node.attrs.string);

        var $button = $('<button type="button">').addClass('btn btn-sm').append($div).append($span);
        this._add_on_click_action($button, node);
        this._handle_attributes($button, node);
        return $button;
    },
    _render_tag_group: function(node) {
        var self = this;
        var is_outer_group = _.some(node.children, function(child) {
            return child.tag === 'group';
        });
        if (!is_outer_group) {
            return this._render_inner_group(node);
        }
        var $result = $('<div class="o_group"/>');

        _.each(node.children, function(child) {
            if (child.tag === 'group') {
                $result.append(self._render_inner_group(child));
            } else {
                $result.append(self._render_node(child));
            }
        });
        return $result;
    },
    _render_inner_group: function(node) {
        var $result = $('<table class="o_group o_inner_group o_group_col_6"/>');
        this._handle_attributes($result, node);
        if (node.attrs.string) {
            var $sep = $('<tr><td colspan="2" style="width:100%;"><div class="o_horizontal_separator">' + node.attrs.string + '</div></td></tr>');
            $result.append($sep);
        }
        var children = node.children;
        for (var i = 0; i < children.length; i++) {
            if (children[i].tag === 'field') {
                $result = this._render_inner_group_field($result, children[i]);
            } else if (children[i].tag === 'label') {
                var label =  children[i];
                // If there is a "for" attribute, we expect to have an id concerned in the next node.
                if (label.attrs.for) {
                    var linked_node = children[i+1];
                    $result = this._render_inner_group_label($result, label, linked_node);
                    i++; // Skip the rendering of the next node because we just did it.
                } else {
                    $result = this._render_inner_group_label($result, label);
                }
            } else {
                var $td = $('<td colspan="2" style="width:100%;">').append(this._render_node(children[i]));
                $result.append($('<tr>').append($td));
            }
        }
        return $result;
    },
    _render_inner_group_field: function ($result, node) {
        return $result.append(this._render_inner_field(node));
    },
    _render_inner_group_label: function ($result, label, linked_node) {
        var $first = $('<td class="o_td_label">')
                    .append(this._render_node(label));
        var $second = linked_node ? $('<td>').append(this._render_node(linked_node)) : $('<td>');
        var $tr = $('<tr>').append($first).append($second);
        return $result.append($tr);
    },
    _render_inner_field: function(node) {
        var field_descr = node.attrs.string || this.fields[node.attrs.name].string;
        var $label = $('<label>')
                        .addClass('o_form_label')
                        .attr('for', this._get_id_for_label(node.attrs.name))
                        .text(field_descr);
        var widget = this._render_field_widget(node);
        if (!widget.is_set() && this.mode === 'readonly') {
            $label.addClass('o_form_label_empty');
        }
        this._handle_attributes($label, node);
        return $('<tr>')
                .append($('<td class="o_td_label">').append($label))
                .append($('<td style="width: 100%">').append(widget.$el));
    },
    _render_tag_notebook: function(node) {
        var self = this;
        var $headers = $('<ul class="nav nav-tabs">');
        var $pages = $('<div class="tab-content nav nav-tabs">');
        _.each(node.children, function(child, index) {
            var page_id = _.uniqueId('notebook_page_');
            var $header = self._render_tab_header(child, page_id);
            var $page = self._render_tab_page(child, page_id);
            if (index === 0) {
                $header.addClass('active');
                $page.addClass('active');
            }
            self._handle_attributes($header, child);
            $headers.append($header);
            $pages.append($page);
        });
        return $('<div class="o_notebook">')
                .data('name', node.attrs.name || '_default_')
                .append($headers)
                .append($pages);
    },
    _render_tab_header: function(page, page_id) {
        var $a = $('<a>', {
            'data-toggle': 'tab',
            disable_anchor: 'true',
            href: '#' + page_id,
            role: 'tab',
            text: page.attrs.string,
        });
        return $('<li>').append($a);
    },
    _render_tab_page: function(page, page_id) {
        var $result = $('<div class="tab-pane" id="' + page_id + '">');
        $result.append(_.map(page.children, this._render_node.bind(this)));
        return $result;
    },
    _render_button_box: function(node) {
        var $result = $('<' + node.tag + '>', { 'class': 'o_not_full' });
        // Avoid to show buttons if we are in create mode (edit mode without res_id)
        if (this.mode === 'edit' && !this.state.res_id) {
            return $result;
        }
        var buttons = _.map(node.children, this._render_stat_button.bind(this));
        var buttons_partition = _.partition(buttons, function($button) {
            return $button.is('.o_form_invisible');
        });
        var invisible_buttons = buttons_partition[0];
        var visible_buttons = buttons_partition[1];

        // Get the unfolded buttons according to window size
        var nb_buttons = [2, 4, 6, 7][config.device.size_class];
        var unfolded_buttons = visible_buttons.slice(0, nb_buttons).concat(invisible_buttons);

        // Get the folded buttons
        var folded_buttons = visible_buttons.slice(nb_buttons);
        if(folded_buttons.length === 1) {
            unfolded_buttons = buttons;
            folded_buttons = [];
        }

        // Toggle class to tell if the button box is full (LESS requirement)
        var full = (visible_buttons.length > nb_buttons);
        $result.toggleClass('o_full', full).toggleClass('o_not_full', !full);

        // Add the unfolded buttons
        _.each(unfolded_buttons, function($button) {
            $button.appendTo($result);
        });

        // Add the dropdown with folded buttons if any
        if(folded_buttons.length) {
            $result.append($("<button>", {
                type: 'button',
                'class': "btn btn-sm oe_stat_button o_button_more dropdown-toggle",
                'data-toggle': "dropdown",
                text: _t("More"),
            }));

            var $ul = $("<ul>", {'class': "dropdown-menu o_dropdown_more", role: "menu"});
            _.each(folded_buttons, function($button) {
                $('<li>').appendTo($ul).append($button);
            });
            $ul.appendTo($result);
        }

        this._handle_attributes($result, node);
        return $result;
    },
    _render_stat_button: function(node) {
        var $button = $('<button>').addClass('btn btn-sm oe_stat_button');
        if (node.attrs.icon) {
            $('<div>')
                .addClass('fa fa-fw o_button_icon')
                .addClass(node.attrs.icon)
                .appendTo($button);
        }
        $button.append(_.map(node.children, this._render_node.bind(this)));
        this._add_on_click_action($button, node);
        this._handle_attributes($button, node);
        return $button;
    },
    _add_on_click_action: function($el, node) {
        var self = this;
        $el.click(function() {
            self.trigger_up('call_button', {
                attrs: node.attrs,
                show_wow: self.$el.hasClass('o_wow'),  // TODO: implement this (in view)
            });
        });
    },
    _get_field_values: function(data) {
        return _.mapObject(data, function (value) {
            return {value: value};
        });
    },
    _get_id_for_label: function(name) {
        var id_for_label = this.ids_for_labels[name];
        if (!id_for_label) {
            id_for_label = _.uniqueId('o_field_input_');
            this.ids_for_labels[name] = id_for_label;
        }
        return id_for_label;
    },
    _handle_attributes: function($el, node) {
        var modifiers = JSON.parse(node.attrs.modifiers || "{}");
        if ('invisible' in modifiers) {
            var is_invisible = data.compute_domain(modifiers.invisible, this.field_values);
            if (is_invisible) {
                $el.addClass('o_form_invisible');
            }
        }
        if (node.attrs.class) {
            $el.addClass(node.attrs.class);
        }
    },
});

});

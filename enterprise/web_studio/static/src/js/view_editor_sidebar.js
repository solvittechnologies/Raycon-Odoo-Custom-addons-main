odoo.define('web_studio.ViewEditorSidebar', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var relational_fields = require('web.relational_fields');
var Widget = require('web.Widget');
var FieldManagerMixin = require('web_studio.FieldManagerMixin');

var _t = core._t;

return Widget.extend(FieldManagerMixin, {
    template: 'web_studio.ViewEditorSidebar',
    custom_events: _.extend({}, FieldManagerMixin.custom_events, {
        field_changed: function(event) {
            this.change_field_group(event);
        },
    }),
    events: {
        'click .o_web_studio_view': function() {
            this.trigger_up('unselect_element');
            this.toggle_mode('view');
        },
        'click .o_web_studio_xml_editor': 'on_xml_editor',
        'click .o_display_view .o_web_studio_parameters': 'on_view_parameters',
        'click .o_display_field .o_web_studio_parameters': 'on_field_parameters',
        'change #show_invisible': 'toggle_form_invisible',
        'click .o_web_studio_remove': 'remove_element',
        'change .o_display_view input, .o_display_view select': 'change_view',
        'change .o_display_field input': 'change_element',
        'change .o_display_page input': 'change_element',
        'change .o_display_group input': 'change_element',
        'change .o_display_button input': 'change_element',
    },

    init: function (parent, view_type, view_attrs) {
        FieldManagerMixin.init.call(this);
        this._super.apply(this, arguments);
        this.debug = core.debug;
        this.mode = 'view';
        this.view_type = view_type;
        this.view_attrs = view_attrs || {};
    },
    toggle_mode: function(mode, options) {
        if (options && options.field) {
            this.field_parameters = options.field;
            this.node = options.node;
            this.attrs = options.field.__attrs;
            this.modifiers = JSON.parse(options.field.__attrs.modifiers);
            this.compute_field_attrs();
        } else if (options && options.page) {
            this.node = options.page;
            this.attrs = options.page.attrs;
        } else if (options && options.group) {
            this.node = options.group;
            this.attrs = options.group.attrs;
        } else if (options && options.button) {
            this.node = options.button;
            this.attrs = options.button.attrs;
        }

        this.mode = mode;
        var mode_tag_map = {
            field: 'field',
            page: 'page',
            group: 'group',
            button: 'button',
        };
        this.tag = mode in mode_tag_map ? mode_tag_map[mode] : 'div';

        this.renderElement();

        if (this.mode === 'field') {
            var studio_groups = this.attrs.studio_groups ? JSON.parse(this.attrs.studio_groups) : [];
            var record_id = this.datamodel.make_record('ir.model.fields', [{
                name: 'groups',
                relation: 'res.groups',
                relational_value: studio_groups,
                type: 'many2many',
                value: _.pluck(studio_groups, 'id'),
            }]);
            var many2many_options = {
                id_for_label: 'groups',
                mode: 'edit',
                no_quick_create: true,  // FIXME: enable add option
            };
            var Many2ManyTags = relational_fields.FieldMany2ManyTags;
            this.many2many = new Many2ManyTags(this, 'groups', this.datamodel.get(record_id), many2many_options);
            this.many2many.appendTo(this.$el.find('.o_groups'));
        }
    },
    compute_field_attrs: function() {
        /* Compute field attributes.
         * These attributes are either taken from modifiers or attrs
         * so attrs store their combinaison.
         */
        this.attrs.invisible = this.modifiers.invisible || this.modifiers.tree_invisible;
        this.attrs.readonly = this.modifiers.readonly;
        this.attrs.string = this.attrs.string || this.field_parameters.string;
        this.attrs.help = this.attrs.help || this.field_parameters.help;
        this.attrs.placeholder = this.attrs.placeholder || this.field_parameters.placeholder;
        this.attrs.required = this.field_parameters.required || this.modifiers.required;
        this.attrs.domain = this.attrs.domain || this.field_parameters.domain;
        this.attrs.context = this.attrs.context || this.field_parameters.context;
    },
    on_xml_editor: function () {
        this.trigger_up('open_xml_editor');
    },
    on_view_parameters: function() {
        this.trigger_up('open_view_form');
    },
    on_field_parameters: function() {
        this.trigger_up('open_field_form', {field_name: this.node.attrs.name});
    },
    toggle_form_invisible: function(ev) {
        this.trigger_up('toggle_form_invisible', ev);
    },
    change_view: function(ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (attribute) {
            var new_attrs = {};
            if ($input.attr('type') === 'checkbox') {
                new_attrs[attribute] = $input.is(':checked') === true ? '': 'false';
            } else {
                new_attrs[attribute] = $input.val();
            }
            this.trigger_up('view_change', {
                type: 'attributes',
                structure: 'view_attribute',
                new_attrs: new_attrs,
            });
            _.extend(this.view_attrs, new_attrs);
        }
    },
    change_element: function(ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (attribute) {
            var new_attrs = {};
            if ($input.attr('type') === 'checkbox') {
                new_attrs[attribute] = $input.is(':checked') === true ? 'True': 'False';
            } else {
                new_attrs[attribute] = $input.val();
            }
            this.trigger_up('view_change', {
                type: 'attributes',
                structure: 'edit_attributes',
                node: this.node,
                new_attrs: new_attrs,
            });
            _.extend(this.attrs, new_attrs);
        }
    },
    change_field_group: function() {
        var new_attrs = {};
        new_attrs.groups = this.many2many.value;
        this.trigger_up('view_change', {
            type: 'attributes',
            structure: 'edit_attributes',
            node: this.node,
            new_attrs: new_attrs,
        });

        _.extend(this.attrs, new_attrs);
    },
    remove_element: function() {
        var self = this;
        var attrs;
        var message;

        if (this.mode === 'chatter') {
            attrs = { 'class': 'oe_chatter' };
            message = _t('Are you sure you want to remove the chatter from the view?');
        } else {
            attrs = _.pick(this.attrs, 'name');
            message = _.str.sprintf(_t('Are you sure you want to remove this %s form the view?'), this.tag);
        }

        Dialog.confirm(this, message, {
            confirm_callback: function() {
                self.trigger_up('view_change', {
                    type: 'remove',
                    structure: 'remove',
                    node: {
                        tag: self.tag,
                        attrs: attrs,
                    },
                });
                self.toggle_mode('view');
            }
        });
    },
});

});

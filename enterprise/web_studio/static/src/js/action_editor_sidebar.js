odoo.define('web_studio.ActionEditorSidebar', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var relational_fields = require('web.relational_fields');
var Widget = require('web.Widget');

var FieldManagerMixin = require('web_studio.FieldManagerMixin');

return Widget.extend(FieldManagerMixin, {
    template: 'web_studio.ActionEditorSidebar',
    custom_events: _.extend({}, FieldManagerMixin.custom_events, {
        field_changed: function(event) {
            this.field_changed(event);
        },
    }),
    events: {
        'change input, textarea': 'change_action',
        'click .o_web_studio_parameters': 'on_parameters',
    },

    init: function (parent, action) {
        FieldManagerMixin.init.call(this);
        this._super.apply(this, arguments);
        this.debug = core.debug;
        this.action = action;
        this.action_attrs = {
            name: action.display_name || action.name,
            help: action.help && action.help.replace(/\n\s+/g, '\n') || '',
        };
        this.groups_info = [];
    },

    willStart: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            if (self.action.groups_id.length === 0) { return; }

            // many2many field expects to receive: a list of {id, name, display_name}
            var def = new Model('res.groups')
                .query(['id', 'name', 'display_name'])
                .filter([['id', 'in', self.action.groups_id]])
                .all();

            return def.then(function(result) {
                self.groups_info = result;
            });
        });
    },

    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {

            var groups = self.action.groups_id;
            var record_id = self.datamodel.make_record('ir.actions.act_window', [{
                name: 'groups_id',
                relation: 'res.groups',
                relational_value: self.groups_info,
                type: 'many2many',
                value: groups,
            }]);
            var many2many_options = {
                mode: 'edit',
                no_quick_create: true,  // FIXME: enable add option
            };
            var Many2ManyTags = relational_fields.FieldMany2ManyTags;
            self.many2many = new Many2ManyTags(self, 'groups_id', self.datamodel.get(record_id), many2many_options);
            self.many2many.appendTo(self.$el.find('.o_groups'));
        });
    },

    change_action: function(ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (attribute) {
            var new_attrs = {};
            new_attrs[attribute] = $input.val();
            this.trigger_up('studio_edit_action', {args: new_attrs});
        }
    },

    on_parameters: function() {
        this.trigger_up('open_action_form');
    },

    field_changed: function(ev) {
        var args = {};
        args[ev.data.name] = this.many2many.value;
        this.trigger_up('studio_edit_action', {args: args});
    },
});

});

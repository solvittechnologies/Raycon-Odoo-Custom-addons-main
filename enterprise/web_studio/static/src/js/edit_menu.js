odoo.define('web_studio.EditMenu', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var form_common = require('web.form_common');
var Model = require('web.Model');
var relational_fields = require('web.relational_fields');
var Widget = require('web.Widget');

var FieldManagerMixin = require('web_studio.FieldManagerMixin');

var customize = require('web_studio.customize');

var _t = core._t;

var EditMenu = Widget.extend({
    template: 'web_studio.EditMenu',
    events: {
        'click .o_web_edit_menu': 'on_click',
    },

    init: function(parent, menu_data, current_primary_menu) {
        this._super.apply(this, arguments);
        this.menu_data = menu_data;
        this.current_primary_menu = current_primary_menu;
    },

    on_click: function (event) {
        event.preventDefault();
        new EditMenuDialog(this, this.menu_data, this.current_primary_menu).open();
    },
});

var EditMenuDialog = Dialog.extend({
    template: 'web_studio.EditMenu_wizard',
    events: _.extend({}, Dialog.prototype.events, {
        'click a.js_add_menu': 'add_menu',
        'click button.js_edit_menu': 'edit_menu',
        'click button.js_delete_menu': 'delete_menu',
    }),

    init: function(parent, menu_data, current_primary_menu) {
        var options = {
            title: _t('Edit Menu'),
            subtitle: _t('Drag a menu to the right to create a sub-menu'),
            size: 'medium',
            buttons: [
                {text: _t("Confirm"), classes: 'btn-primary', click: _.bind(this.save, this)},
                {text: _t("Cancel"), close: true},
            ],
        };
        this.current_primary_menu = current_primary_menu;
        this.roots = this.get_menu_data_filtered(menu_data);

        this.to_delete = [];
        this.to_move = {};

        this._super(parent, options);
    },

    start: function () {

        this.$('.oe_menu_editor').nestedSortable({
            listType: 'ul',
            handle: 'div',
            items: 'li',
            maxLevels: 5,
            toleranceElement: '> div',
            forcePlaceholderSize: true,
            opacity: 0.6,
            placeholder: 'oe_menu_placeholder',
            tolerance: 'pointer',
            attribute: 'data-menu-id',
            expression: '()(.+)', // nestedSortable takes the second match of an expression (*sigh*)
            relocate: this.move_menu.bind(this),
        });

        return this._super.apply(this, arguments);
    },

    get_menu_data_filtered: function(menu_data) {
        var self = this;
        var menus = menu_data.children.filter(function (el) {
            return el.id === self.current_primary_menu;
        });
        return menus;
    },

    add_menu: function (ev) {
        ev.preventDefault();

        var self = this;
        var form = new NewMenuDialog(this, this.current_primary_menu).open();
        form.on('record_saved', self, function() {
            self._saveChanges().then(function () {
                self._reload_menu_data(true);
            });
        });
    },

    delete_menu: function (ev) {
        var $menu = $(ev.currentTarget).closest('[data-menu-id]');
        var menu_id = $menu.data('menu-id') || 0;
        if (menu_id) {
            this.to_delete.push(menu_id);
        }
        $menu.remove();
    },

    edit_menu: function (ev) {
        var self = this;
        var menu_id = $(ev.currentTarget).closest('[data-menu-id]').data('menu-id');
        var form = new form_common.FormViewDialog(this, {
            res_model: 'ir.ui.menu',
            res_id: menu_id,
        }).open();

        form.on('record_saved', this, function() {
            self._saveChanges().then(function () {
                self._reload_menu_data(true);
            });
        });
    },

    move_menu: function (ev, ui) {
        var self = this;

        var $menu = $(ui.item);
        var menu_id = $menu.data('menu-id');

        this.to_move[menu_id] = {
            parent_id: $menu.parents('[data-menu-id]').data('menu-id') || this.current_primary_menu,
            sequence: $menu.index(),
        };

        // Resequence siblings
        _.each($menu.siblings('li'), function(el) {
            var menu_id = $(el).data('menu-id');
            if (menu_id in self.to_move) {
                self.to_move[menu_id].sequence = $(el).index();
            } else {
                self.to_move[menu_id] = {sequence: $(el).index()};
            }
        });
    },

    save: function () {
        var self = this;

        return this._saveChanges().then(function(){
            self._reload_menu_data();
            self.close();
        });
    },

    /**
     * Save the current changes (in `to_move` and `to_delete`).
     *
     * @private
     * @returns {Deferred}
     */
    _saveChanges: function () {
        return new Model('ir.ui.menu').call('customize', [], {
            to_move: this.to_move,
            to_delete: this.to_delete,
        });
    },

    _reload_menu_data: function(keep_open) {
        this.trigger_up('reload_menu_data', {keep_open: keep_open});
    },
});

var NewMenuDialog = Dialog.extend(FieldManagerMixin, {
    template: 'web_studio.EditMenu_new',

    init: function(parent, parent_id) {
        this.parent_id = parent_id;
        var options = {
            title: _t('Create a new Menu'),
            size: 'medium',
            buttons: [
                {text: _t("Confirm"), classes: 'btn-primary', click: _.bind(this.save, this)},
                {text: _t("Cancel"), close: true},
            ],
        };
        FieldManagerMixin.init.call(this);
        this._super(parent, options);

        var self = this;
        this.opened().then(function () {
            // focus on input
            self.$el.find('input[name="name"]').focus();
        });
    },
    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            var record_id = self.datamodel.make_record('ir.actions.act_window', [{
                name: 'model',
                relation: 'ir.model',
                type: 'many2one',
            }]);
            var options = {
                mode: 'edit',
                no_quick_create: true,  // FIXME: enable add option
            };
            var Many2One = relational_fields.FieldMany2One;
            self.many2one = new Many2One(self, 'model', self.datamodel.get(record_id), options);
            self.many2one.appendTo(self.$('.js_model'));
        });
    },
    save: function() {
        var self = this;

        var name = this.$el.find('input').first().val();
        var model_id = this.many2one.value;

        return customize.create_new_menu(name, this.parent_id, model_id).then(function(){
                self.trigger('record_saved');
                self.close();
            });
    },


});

return EditMenu;

});

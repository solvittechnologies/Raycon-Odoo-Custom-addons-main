odoo.define('web_studio.Main', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var data_manager = require('web.data_manager');
var framework = require('web.framework');
var form_common = require('web.form_common');
var Widget = require('web.Widget');

var bus = require('web_studio.bus');
var customize = require('web_studio.customize');
var ActionEditor = require('web_studio.ActionEditor');
var ViewEditorManager = require('web_studio.ViewEditorManager');

var _t = core._t;
var _lt = core._lt;

var Main = Widget.extend({
    className: 'o_web_studio_client_action',
    error_messages: {
        'wrong_xpath': _lt("This operation caused an error, probably because a xpath was broken"),
        'view_rendering': _lt("The requested change caused an error in the view. It could be because a field was deleted, but still used somewhere else."),
    },

    custom_events: {
        'studio_default_view': 'default_view',
        'studio_disable_view': 'disable_view',
        'studio_edit_view': 'edit_view',
        'studio_new_view': 'new_view',
        'studio_set_another_view': 'set_another_view',
        'studio_edit_action': 'edit_action',
        'studio_error': '_show_error',
    },

    init: function (parent, context, options) {
        this._super.apply(this, arguments);
        this.action = options.action;
        this.active_view = options.active_view;
        this.ids = options.ids;
        this.res_id = options.res_id;
        this.chatter_allowed = options.chatter_allowed;
    },

    willStart: function () {
        if (!this.action) {
            return $.Deferred().reject();
        }
        return this._super.apply(this, arguments);
    },

    start: function () {
        this.set('title', _t('Studio'));
        // we try to directly edit the active view instead of going to the action editor
        if (this.active_view) {
            return this.edit_view({data: {view_type: this.active_view}});
        } else {
            var active_view_types = this.action.view_mode.split(',');
            this.action_editor = new ActionEditor(this, this.action, active_view_types);
            return $.when(this.action_editor.appendTo(this.$el), this._super.apply(this, arguments));
        }
    },

    edit_action: function (event) {
        var self = this;

        var args = event.data.args;
        if (!args) { return; }

        customize.edit_action(this.action, args).then(function(result) {
            self.action = result;
        });
    },

    edit_view: function (event) {
        var self = this;
        var context = _.extend({}, this.action.context, { studio: true}); // Add studio mode in session context instead?
        var view_type = event.data.view_type;
        var dataset = new data.DataSetSearch(this, this.action.res_model, context, this.action.domain);

        var options = {};
        var views = this.action.views.slice();

        // search is not in action.view
        options.load_filters = true;
        var searchview_id = this.action.search_view_id && this.action.search_view_id[0];
        views.push([searchview_id || false, 'search']);

        var view = _.find(views, function(el) { return el[1] === view_type; });
        var view_id = view && view[0];

        // The default view needs to be created before `load_views` or the renderer will not be aware that a new view exists
        return customize.get_studio_view_arch(this.action.res_model, view_type, view_id).then(function(studio_view) {
            return data_manager.load_views(dataset, views, options).then(function (fields_views) { // todo: call with same arguments as ViewManager
                var options = {
                    ids: self.ids,
                    res_id: self.res_id,
                    chatter_allowed: self.chatter_allowed,
                    studio_view_id: studio_view.studio_view_id,
                    studio_view_arch: studio_view.studio_view_arch,
                };
                self.view_editor = new ViewEditorManager(self, self.action.res_model, fields_views[view_type], view_type, options);

                var fragment = document.createDocumentFragment();
                return self.view_editor.appendTo(fragment).then(function () {
                    if (self.action_editor) {
                        framework.detach([{widget: self.action_editor}]);
                    }
                    framework.append(self.$el, [fragment], {
                        in_DOM: true,
                        callbacks: [{widget: self.view_editor}],
                    });

                    bus.trigger('edition_mode_entered', view_type);
                });
            });
        });
    },

    default_view: function (event) {
        var view_type = event.data.view_type;
        var view_mode = _.without(this.action.view_mode.split(','), view_type);
        view_mode.unshift(view_type);
        view_mode = view_mode.toString();

        this._write_view_mode(view_mode);
    },

    disable_view: function (event) {
        var view_type = event.data.view_type;
        var view_mode = _.without(this.action.view_mode.split(','), view_type).toString();

        this._write_view_mode(view_mode);
    },

    new_view: function (event) {
        var view_type = event.data.view_type;
        var view_mode = this.action.view_mode + ',' + view_type;

        this._write_view_mode(view_mode);
    },

    set_another_view: function (event) {
        var self = this;
        var view_mode = event.data.view_mode;

        new form_common.SelectCreateDialog(this, {
            res_model: 'ir.ui.view',
            title: _t('Select a view'),
            disable_multiple_selection: true,
            no_create: true,
            domain: [
                ['type', '=', view_mode],
                ['mode', '=', 'primary'],
                ['model', '=', this.action.res_model],
            ],
            on_selected: function (view_id) {
                self._set_another_view(view_mode, view_id[0]);
            }
        }).open();
    },

    _write_view_mode: function(view_mode) {
        var self = this;
        return customize.edit_action(this.action, {view_mode: view_mode}).then(function(result) {
            self.do_action('action_web_studio_main', {
                action: result,
            });
        });
    },

    _set_another_view: function(view_mode, view_id) {
        var self = this;
        return customize.set_another_view(this.action.id, view_mode, view_id).then(function(result) {
            self.do_action('action_web_studio_main', {
                action: result,
            });
        });
    },

    _show_error: function(event) {
        this.do_warn(_t("Error"), this.error_messages[event.data.error]);
    },
});

core.action_registry.add('action_web_studio_main', Main);

});

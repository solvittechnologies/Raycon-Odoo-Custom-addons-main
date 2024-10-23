odoo.define('web_studio.ActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');


// Includes the ActionManger to handle stashing and restoring of the action stack
ActionManager.include({
    stash_action_stack: function () {
        if (this.stashed_action_stack) {
            console.warn('An action stack has already been stashed');
        }
        this.stashed_action_stack = this.action_stack;
        this.action_stack = [];
    },
    restore_action_stack: function () {
        var self = this;
        var def;
        var to_destroy = this.action_stack;
        var last_action = _.last(this.stashed_action_stack);
        this.action_stack = this.stashed_action_stack;
        this.stashed_action_stack = undefined;
        if (last_action && last_action.action_descr.id) {
            var view_type = last_action.get_active_view && last_action.get_active_view();
            var res_id = parseInt($.deparam(window.location.hash.slice(1)).id);

            // The action could have been modified (name, view_ids, etc.)
            // so we need to use do_action to reload it.
            def = this.do_action(last_action.action_descr.id, {
                view_type: view_type,
                replace_last_action: true,
                res_id: res_id,
                additional_context: last_action.action_descr.context,
            });
        } else {
            def = $.Deferred().reject();
        }
        return def.fail(function () {
            self.clear_action_stack();
            self.trigger_up('show_app_switcher');
        }).always(this.clear_action_stack.bind(this, to_destroy));
    },
});

});

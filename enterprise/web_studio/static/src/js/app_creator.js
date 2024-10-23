odoo.define('web_studio.AppCreator', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var relational_fields = require('web.relational_fields');

var bus = require('web_studio.bus');
var customize = require('web_studio.customize');
var FieldManagerMixin = require('web_studio.FieldManagerMixin');
var IconCreator = require('web_studio.IconCreator');

var QWeb = core.qweb;
var _t = core._t;

var AppCreator = Widget.extend(FieldManagerMixin, {
    template: 'web_studio.AppCreator',
    events: {
        'click .o_web_studio_app_creator_next': 'on_next',
        'click .o_app_creator_back': 'on_back',
        'click .o_web_studio_app_creator_leave': 'on_leave',
    },

    init: function () {
        this.current_step = 1;
        FieldManagerMixin.init.call(this);
        this._super.apply(this, arguments);
    },
    start: function () {
        this.$left = this.$('.o_web_studio_app_creator_left_content');
        this.$right = this.$('.o_web_studio_app_creator_right_content');
        this.update();
        return this._super.apply(this, arguments);
    },

    on_next: function () {
        var self = this;

        if (this.current_step === 1) {
            this.current_step++;
            this.update();
        } else {
            var name = this.$left.find('input').first().val() || _t('My App');
            var model_id = this.many2one.value;
            var icon = this.icon_creator.get_value();

            if (!model_id) {
                Dialog.alert(this, _t("Please set a model."));
                return;
            }

            this.$('.o_web_studio_app_creator_next').prop('disabled', true);
            customize.create_new_app(name, model_id, icon).then(function(result) {
                self.trigger_up('new_app_created', result);
            });
        }
    },
    on_back: function () {
        this.current_step--;
        this.update();
    },
    on_leave: function () {
        this.trigger_up('show_app_switcher');
        bus.trigger('studio_toggled', false);
        web_client.action_manager.clear_action_stack(); // fixme + remove Back in app switcher navbar
    },

    update: function () {
        this.$left.empty();
        this.$right.empty();
        if (this.current_step === 1) {
            this.$left.append($(QWeb.render('web_studio.AppCreator.Welcome')));
            this.$right.append($('<img>', {
                src: "/web_enterprise/static/src/img/default_icon_app.png"
            }));
        } else {
            var $app_form= $(QWeb.render('web_studio.AppCreator.Form'));

            var record_id = this.datamodel.make_record('ir.actions.act_window', [{
                name: 'model',
                relation: 'ir.model',
                type: 'many2one',
                domain: [['transient', '=', false], ['abstract', '=', false]]
            }]);
            var options = {
                mode: 'edit',
                no_quick_create: true,  // FIXME: enable add option
            };
            var Many2one = relational_fields.FieldMany2One;
            this.many2one = new Many2one(this, 'model', this.datamodel.get(record_id), options);
            this.many2one.appendTo($app_form.find('.js_model'));

            this.$left.append($app_form);

            // focus on input
            this.$el.find('input[name="name"]').focus();

            this.icon_creator = new IconCreator(this);
            this.icon_creator.appendTo(this.$right);
        }
        this.$('.o_app_creator_back').toggleClass('o_hidden', (this.current_step === 1));
    }
});

core.action_registry.add('action_web_studio_app_creator', AppCreator);

});

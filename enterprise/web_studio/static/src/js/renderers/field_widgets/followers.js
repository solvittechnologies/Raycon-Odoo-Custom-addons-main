odoo.define('web_studio.Followers', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var Dialog = require('web.Dialog');
var session = require('web.session');

var _t = core._t;
var QWeb = core.qweb;


// -----------------------------------------------------------------------------
// Followers Widget ('mail_followers' widget)
//
// Note: the followers widget is moved inside the chatter for layout purposes
// -----------------------------------------------------------------------------
var Followers = AbstractField.extend({
    template: 'mail.Followers',

    events: {
        // click on '(Un)Follow' button, that toggles the follow for uid
        'click .o_followers_follow_button': function () {
            if (!this.is_follower) {
                this.do_follow();
            } else {
                this.do_unfollow({user_ids: [session.uid]});
            }
        },
        // click on a subtype, that (un)subscribes for this subtype
        'click .o_subtypes_list input': function (event) {
            event.stopPropagation();
            this.do_update_subscription(event);
            var $list = this.$('.o_subtypes_list');
            if (!$list.hasClass('open')) {
                $list.addClass('open');
            }
            if (this.$('.o_subtypes_list ul')[0].children.length < 1) {
                $list.removeClass('open');
            }
        },
        // click on 'invite' button, that opens the invite wizard
        'click .o_add_follower': function (event) {
            event.preventDefault();
            this.on_invite_follower(false);
        },
        'click .o_add_follower_channel': function (event) {
            event.preventDefault();
            this.on_invite_follower(true);
        },
        // click on 'edit_subtype(pencil)' button to edit subscription
        'click .o_edit_subtype': 'on_edit_subtype',
        'click .o_remove_follower': 'on_remove_follower',
        'click .o_mail_redirect': 'on_redirect',
    },

    init: function(parent, name, record, options) {
        this._super.apply(this, arguments);

        this.image = this.field.__attrs.image || 'image_small';
        this.comment = this.field.__attrs.help || false;

        this.followers = [];
        this.data_subtype = {};
        this.is_follower = undefined;

        options = options || {};
        this.view_is_editable = options.view_is_editable;
    },

    willStart: function () {
        var self = this;
        this.followers_def = $.Deferred();
        this.trigger_up('perform_rpc', {
            route: '/mail/read_followers',
            args: [this.value, this.model],
            on_success: function (results) {
                self.followers = results.followers;
                self.subtypes = results.subtypes;
                var user_follower = _.filter(self.followers, function (rec) { return rec.is_uid; });
                self.is_follower = user_follower.length >= 1;
                self.followers_def.resolve();
            },
            on_fail: function () {
                self.loading_error = true;
                self.followers_def.resolve();
            },
        });
        return $.when(this.followers_def, this._super.apply(this, arguments));
    },

    is_set: function () {
        return true;
    },

    render: function () {
        if (this.loading_error) {
            this.display_generic();
        } else {
            this.display_followers(this.followers);
            if (this.subtypes) { // current user is follower
                this.display_subtypes(this.subtypes);
            }
            this.display_buttons();
        }
    },

    display_buttons: function () {
        if (this.is_follower) {
            this.$('button.o_followers_follow_button').removeClass('o_followers_notfollow').addClass('o_followers_following');
            this.$('.o_subtypes_list > .dropdown-toggle').attr('disabled', false);
            this.$('.o_followers_actions .dropdown-toggle').addClass('o_followers_following');
        } else {
            this.$('button.o_followers_follow_button').removeClass('o_followers_following').addClass('o_followers_notfollow');
            this.$('.o_subtypes_list > .dropdown-toggle').attr('disabled', true);
            this.$('.o_followers_actions .dropdown-toggle').removeClass('o_followers_following');
        }
    },

    /** Read on res.partner failed: only display the number of followers */
    display_generic: function () {
        this.$('.o_followers_actions').hide();
        this.$('.o_followers_list').hide();
        this.$('.o_followers_title_box > button').prop('disabled', true);
        this.$('.o_followers_count').html(this.value.length).parent().attr("title", this._format_followers(this.value.length));
    },

    /** Display the followers */
    display_followers: function () {
        var self = this;

        // clean and display title
        var $followers_list = this.$('.o_followers_list').empty();
        this.$('.o_followers_count').html(this.value.length).parent().attr("title", this._format_followers(this.value.length));

        // render the dropdown content
        $(QWeb.render('mail.Followers.add_more', {widget: this})).appendTo($followers_list);
        var $follower_li;
        _.each(this.followers, function (record) {
            $follower_li = $(QWeb.render('mail.Followers.partner', {
                'record': _.extend(record, {'avatar_url': '/web/image/' + record.res_model + '/' + record.res_id + '/image_small'}),
                'widget': self})
            );
            $follower_li.appendTo($followers_list);

            // On mouse-enter it will show the edit_subtype pencil.
            if (record.is_editable) {
                $follower_li.on('mouseenter mouseleave', function(e) {
                    $(e.currentTarget).find('.o_edit_subtype').toggleClass('hide', e.type === 'mouseleave');
                });
            }
        });
    },

    /** Display subtypes: {'name': default, followed} */
    display_subtypes:function (data, dialog, display_warning) {
        var old_parent_model;
        var $list;
        if (dialog) {
            $list = $('<ul>').appendTo(this.dialog.$el);
        } else {
            $list = this.$('.o_subtypes_list ul');
        }
        $list.empty();

        this.data_subtype = data;

        _.each(data, function (record) {
            if (old_parent_model !== record.parent_model && old_parent_model !== undefined) {
                $list.append($('<li>').addClass('divider'));
            }
            old_parent_model = record.parent_model;
            record.followed = record.followed || undefined;
            $list.append(QWeb.render('mail.Followers.subtype', {
                'record': record,
                'dialog': dialog,
                'display_warning': display_warning && record.internal,
            }));
        });

        if (display_warning) {
            $(QWeb.render('mail.Followers.subtypes.warning')).appendTo(this.dialog.$el);
        }
    },

    _format_followers: function (count){
        var str = '';
        if (count <= 0) {
            str = _t('No follower');
        } else if (count === 1){
            str = _t('One follower');
        } else {
            str = ''+count+' '+_t('followers');
        }
        return str;
    },

    on_edit_subtype: function (event) {
        var self = this;
        var $currentTarget = $(event.currentTarget);
        var follower_id = $currentTarget.data('follower-id'); // id of model mail_follower
        this.trigger_up('perform_rpc', {
            route: '/mail/read_subscription_data',
            args: {
                res_model: this.model,
                follower_id: follower_id,
            },
            on_success: function (data) {
                var res_id = $currentTarget.data('oe-id'); // id of model res_partner or mail_channel
                var is_channel = $currentTarget.data('oe-model') === 'mail.channel';
                self.dialog = new Dialog(this, {
                    size: 'medium',
                    title: _t('Edit Subscription of ') + $currentTarget.siblings('a').text(),
                    buttons: [
                        {
                            text: _t("Apply"),
                            classes: 'btn-primary',
                            click: function () {
                                self.do_update_subscription(event, res_id, is_channel);
                            },
                            close: true
                        },
                        {
                            text: _t("Cancel"),
                            close: true,
                        },
                    ],
                }).open();
                self.display_subtypes(data, true, is_channel);
            },
        });
    },

    on_invite_follower: function (channel_only) {
        var action = {
            type: 'ir.actions.act_window',
            res_model: 'mail.wizard.invite',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            name: _t('Invite Follower'),
            target: 'new',
            context: {
                'default_res_model': this.model,
                'default_res_id': this.res_id,
                'mail_invite_follower_channel_only': channel_only,
            },
        };
        this.trigger_up('do_action', {
            action: action,
            options: {
                on_close: this.trigger_up.bind(this, 'reload'), // fixme: only reload this field?
            },
        });
    },

    on_remove_follower: function (event) {
        var res_model = $(event.target).parent().find('a').data('oe-model');
        var res_id = $(event.target).parent().find('a').data('oe-id');
        if (res_model === 'res.partner') {
            return this.do_unfollow({partner_ids: [res_id]});
        } else {
            return this.do_unfollow({channel_ids: [res_id]});
        }
    },

    on_redirect: function (event) {
        event.preventDefault();
        var $target = $(event.target);
            this.trigger_up('do_action', {
            action: {
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_model: $target.data('oe-model'),
                views: [[false, 'form']],
                res_id: $target.data('oe-id'),
            },
        });
    },

    do_follow: function () {
        this.trigger_up('perform_model_rpc', {
            model: this.model,
            method: 'message_subscribe_users',
            args: [
                [this.res_id],
                [session.uid],
                undefined,
                {}, // new data.CompoundContext(this.build_context(), {}) // fixme
            ],
            on_success: this.trigger_up.bind(this, 'reload'), // fixme: only reload this field?
        });
    },

    /**
     * Remove users, partners, or channels from the followers
     * @param {Array} [ids.user_ids] the user ids
     * @param {Array} [ids.partner_ids] the partner ids
     * @param {Array} [ids.channel_ids] the channel ids
     */
    do_unfollow: function (ids) {
        var self = this;
        var def = $.Deferred();
        var text = _t("Warning! \n If you remove a follower, he won't be notified of any email or discussion on this document.\n Do you really want to remove this follower ?");
        Dialog.confirm(this, text, {
            confirm_callback: function () {
                var method;
                var args;
                if (ids.partner_ids || ids.channel_ids) {
                    method = 'message_unsubscribe';
                    args = [
                        [self.res_id],
                        ids.partner_ids,
                        ids.channel_ids,
                        {}, // new data.CompoundContext(self.build_context(), {}) // fixme
                    ];
                } else {
                    method = 'message_unsubscribe_users';
                    args = [
                        [self.res_id],
                        ids.user_ids,
                        {}, // new data.CompoundContext(self.build_context(), {}) // fixme
                    ];
                }
                self.trigger_up('perform_model_rpc', {
                    model: self.model,
                    method: method,
                    args: args,
                    on_success: self.trigger_up.bind(self, 'reload'), // fixme: only reload this field?
                });
                def.resolve();
            },
            cancel_callback: def.reject.bind(def),
        });
        return def;
    },

    do_update_subscription: function (event, follower_id, is_channel) {
        var ids = {};
        var action_subscribe;
        var subtypes;

        if (follower_id !== undefined) {
            // Subtypes edited from the modal
            action_subscribe = 'message_subscribe';
            subtypes = this.dialog.$('input[type="checkbox"]');
            if (is_channel) {
                ids.channel_ids = [follower_id];
            } else {
                ids.partner_ids = [follower_id];
            }
        } else {
            action_subscribe = 'message_subscribe_users';
            subtypes = this.$('.o_followers_actions input[type="checkbox"]');
            ids.user_ids = [session.uid];
        }

        // Get the subtype ids
        var checklist = [];
        _.each(subtypes, function (record) {
            if ($(record).is(':checked')) {
                checklist.push(parseInt($(record).data('id')));
            }
        });

        // If no more subtype followed, unsubscribe the follower
        if (!checklist.length) {
            this.do_unfollow(ids).fail(function () {
                $(event.target).prop("checked", true);
            });
        } else {
            var kwargs = _.extend({}, ids);
            kwargs.subtype_ids = checklist;
            kwargs.context = {}; // new data.CompoundContext(this.build_context(), {}); // fixme
            this.trigger_up('perform_model_rpc', {
                model: this.model,
                method: action_subscribe,
                args: [[this.res_id]],
                kwargs: kwargs,
                on_success: this.trigger_up.bind(this, 'reload'), // fixme: only reload this field?
            });
        }
    },
});

field_registry.add('mail_followers', Followers);

});

odoo.define('web_studio.Chatter', function (require) {
"use strict";

var chat_manager = require('mail.chat_manager');
var composer = require('mail.composer');
var ChatThread = require('mail.ChatThread');
var utils = require('mail.utils');

var AbstractField = require('web.AbstractField');
var config = require('web.config');
var core = require('web.core');
var field_registry = require('web.field_registry');
var form_common = require('web.form_common');
var web_utils = require('web.utils');

var _t = core._t;
var QWeb = core.qweb;


// -----------------------------------------------------------------------------
// Chat Composer for the Chatter
//
// Extends the basic Composer Widget to add 'suggested partner' layer (open
// popup when suggested partner is selected without email, or other
// informations), and the button to open the full composer wizard.
// -----------------------------------------------------------------------------
var ChatterComposer = composer.BasicComposer.extend({
    template: 'mail.chatter.ChatComposer',

    init: function (parent, model, suggested_partners, options) {
        this._super(parent, options);
        this.model = model;
        this.suggested_partners = suggested_partners;
        this.options = _.defaults(this.options, {
            display_mode: 'textarea',
            record_name: false,
            is_log: false,
        });
        if (this.options.is_log) {
            this.options.send_text = _t('Log');
        }
        this.events = _.extend(this.events, {
            'click .o_composer_button_full_composer': 'on_open_full_composer',
        });
    },

    should_send: function () {
        return false;
    },

    preprocess_message: function () {
        var self = this;
        var def = $.Deferred();
        this._super().then(function (message) {
            message = _.extend(message, {
                subtype: 'mail.mt_comment',
                message_type: 'comment',
                content_subtype: 'html',
                context: self.context,
            });

            // Subtype
            if (self.options.is_log) {
                message.subtype = 'mail.mt_note';
            }

            // Partner_ids
            if (!self.options.is_log) {
                var checked_suggested_partners = self.get_checked_suggested_partners();
                self.check_suggested_partners(checked_suggested_partners).done(function (partner_ids) {
                    message.partner_ids = (message.partner_ids || []).concat(partner_ids);
                    // update context
                    message.context = _.defaults({}, message.context, {
                        mail_post_autofollow: true,
                    });
                    def.resolve(message);
                });
            } else {
                def.resolve(message);
            }

        });

        return def;
    },

    /**
    * Send the message on SHIFT+ENTER, but go to new line on ENTER
    */
    prevent_send: function (event) {
        return !event.shiftKey;
    },

    /**
     * Get the list of selected suggested partners
     * @returns Array() : list of 'recipient' selected partners (may not be created in db)
     **/
    get_checked_suggested_partners: function () {
        var self = this;
        var checked_partners = [];
        this.$('.o_composer_suggested_partners input:checked').each(function() {
            var full_name = $(this).data('fullname');
            checked_partners = checked_partners.concat(_.filter(self.suggested_partners, function(item) {
                return full_name === item.full_name;
            }));
        });
        return checked_partners;
    },

    /**
     * Check the additional partners (not necessary registered partners), and open a popup form view
     * for the ones who informations is missing.
     * @param Array : list of 'recipient' partners to complete informations or validate
     * @returns Deferred resolved with the list of checked suggested partners (real partner)
     **/
    check_suggested_partners: function (checked_suggested_partners) {
        var self = this;
        var check_done = $.Deferred();

        var recipients = _.filter(checked_suggested_partners, function (recipient) { return recipient.checked; });
        var recipients_to_find = _.filter(recipients, function (recipient) { return (! recipient.partner_id); });
        var names_to_find = _.pluck(recipients_to_find, 'full_name');
        var recipients_to_check = _.filter(recipients, function (recipient) { return (recipient.partner_id && ! recipient.email_address); });
        var recipient_ids = _.pluck(_.filter(recipients, function (recipient) { return recipient.partner_id && recipient.email_address; }), 'partner_id');

        var names_to_remove = [];
        var recipient_ids_to_remove = [];

        // have unknown names -> call message_get_partner_info_from_emails to try to find partner_id
        var def = $.Deferred();
        if (names_to_find.length > 0) {
            this.trigger_up('perform_model_rpc', {
                model: this.model,
                method: 'message_partner_info_from_emails',
                args: [[this.context.default_res_id], names_to_find],
                on_success: def.resolve.bind(def),
            });
        } else {
            def.resolve([]);
        }

        // for unknown names + incomplete partners -> open popup - cancel = remove from recipients
        $.when(def).pipe(function (result) {
            var emails_deferred = [];
            var recipient_popups = result.concat(recipients_to_check);

            _.each(recipient_popups, function (partner_info) {
                var deferred = $.Deferred();
                emails_deferred.push(deferred);

                var partner_name = partner_info.full_name;
                var partner_id = partner_info.partner_id;
                var parsed_email = utils.parse_email(partner_name);

                var dialog = new form_common.FormViewDialog(self, {
                    res_model: 'res.partner',
                    res_id: partner_id,
                    context: {
                        force_email: true,
                        ref: "compound_context",
                        default_name: parsed_email[0],
                        default_email: parsed_email[1],
                    },
                    title: _t("Please complete partner's informations"),
                    disable_multiple_selection: true,
                }).open();
                dialog.on('closed', self, function () {
                    deferred.resolve();
                });
                dialog.opened().then(function () {
                    dialog.view_form.on('on_button_cancel', self, function () {
                        names_to_remove.push(partner_name);
                        if (partner_id) {
                            recipient_ids_to_remove.push(partner_id);
                        }
                    });
                });
            });
            $.when.apply($, emails_deferred).then(function () {
                var new_names_to_find = _.difference(names_to_find, names_to_remove);
                var def = $.Deferred();
                if (new_names_to_find.length > 0) {
                    self.trigger_up('perform_model_rpc', {
                        model: self.model,
                        method: 'message_partner_info_from_emails',
                        args: [[self.context.default_res_id], new_names_to_find, true],
                        on_success: def.resolve.bind(def),
                    });
                } else {
                    def.resolve([]);
                }
                $.when(def).pipe(function (result) {
                    var recipient_popups = result.concat(recipients_to_check);
                    _.each(recipient_popups, function (partner_info) {
                        if (partner_info.partner_id && _.indexOf(partner_info.partner_id, recipient_ids_to_remove) === -1) {
                            recipient_ids.push(partner_info.partner_id);
                        }
                    });
                }).pipe(function () {
                    check_done.resolve(recipient_ids);
                });
            });
        });
        return check_done;
    },

    on_open_full_composer: function() {
        if (!this.do_check_attachment_upload()){
            return false;
        }

        var self = this;
        var recipient_done = $.Deferred();
        if (this.options.is_log) {
            recipient_done.resolve([]);
        } else {
            var checked_suggested_partners = this.get_checked_suggested_partners();
            recipient_done = this.check_suggested_partners(checked_suggested_partners);
        }
        recipient_done.then(function (partner_ids) {
            var context = {
                default_parent_id: self.id,
                default_body: utils.get_text2html(self.$input.val()),
                default_attachment_ids: _.pluck(self.get('attachment_ids'), 'id'),
                default_partner_ids: partner_ids,
                default_is_log: self.options.is_log,
                mail_post_autofollow: true,
            };

            if (self.context.default_model && self.context.default_res_id) {
                context.default_model = self.context.default_model;
                context.default_res_id = self.context.default_res_id;
            }

            self.trigger_up('do_action', {
                action: {
                    type: 'ir.actions.act_window',
                    res_model: 'mail.compose.message',
                    view_mode: 'form',
                    view_type: 'form',
                    views: [[false, 'form']],
                    target: 'new',
                    context: context,
                },
                options: {
                    on_close: function() {
                        self.trigger('need_refresh');
                        var parent = self.getParent();
                        chat_manager.get_messages({model: parent.model, res_id: parent.res_id});
                    },
                },
                on_success: self.trigger.bind(self, 'close_composer'),
            });
        });
    }
});

// -----------------------------------------------------------------------------
// Document Chatter ('mail_thread' widget)
// -----------------------------------------------------------------------------
var Chatter = AbstractField.extend({
    template: 'mail.Chatter',

    events: {
        "click .o_chatter_button_new_message": "on_open_composer_new_message",
        "click .o_chatter_button_log_note": "on_open_composer_log_note",
    },

    init: function () {
        this._super.apply(this, arguments);
        this.msg_ids = this.value || [];
        this.record_name = this.record_data.display_name;
        this.context = {
            default_res_id: this.res_id || false,
            default_model: this.model || false,
        };
        this.dp = new web_utils.DropPrevious();
        // TODO: remove this
        // this was done to be able to share the template with the legacy
        // composer. Now, the template should be updated and use node_options instead
        this.options = this.node_options;
    },

    willStart: function () {
        return chat_manager.is_ready;
    },

    start: function () {
        var self = this;

        var $container = this.$el.parent();
        if ($container.hasClass('oe_chatter')) {
            this.$el
                .addClass($container.attr("class"))
                .unwrap();
        }

        this.thread = new ChatThread(this, {
            display_order: ChatThread.ORDER.DESC,
            display_document_link: false,
            display_needactions: false,
            squash_close_messages: false,
        });
        this.thread.on('load_more_messages', this, this.load_more_messages);
        this.thread.on('toggle_star_status', this, function (message_id) {
            chat_manager.toggle_star_status(message_id);
        });
        this.thread.on('redirect', this, this.on_redirect);
        this.thread.on('redirect_to_channel', this, this.on_channel_redirect);

        var def1 = this.thread.appendTo(this.$el);
        var def2 = this._super.apply(this, arguments);

        return $.when(def1, def2).then(function () {
            chat_manager.bus.on('new_message', self, self.on_new_message);
            chat_manager.bus.on('update_message', self, self.on_update_message);
        });
    },

    is_set: function () {
        return true;
    },

    fetch_and_render_thread: function (ids, options) {
        var self = this;
        options = options || {};
        options.ids = ids;

        // Ensure that only the last loaded thread is rendered to prevent displaying the wrong thread
        var fetch_def = this.dp.add(chat_manager.get_messages(options));

        // Empty thread and display a spinner after 1s to indicate that it is loading
        this.thread.$el.empty();
        web_utils.reject_after(web_utils.delay(1000), fetch_def).then(function () {
            self.thread.$el.append(QWeb.render('Spinner'));
        });

        return fetch_def.then(function (raw_messages) {
            self.thread.render(raw_messages, {display_load_more: raw_messages.length < ids.length});
        });
    },

    on_post_message: function (message) {
        var self = this;
        var options = {model: this.model, res_id: this.res_id};
        chat_manager
            .post_message(message, options)
            .then(function () {
                self.close_composer();
                if (message.partner_ids.length) {
                    self.refresh_followers(); // refresh followers' list
                }
            })
            .fail(function () {
                // todo: display notification
            });
    },

    /**
     * When a message is correctly posted, fetch its data to render it
     * @param {Number} message_id : the identifier of the new posted message
     * @returns {Deferred}
     */
    on_new_message: function (message) {
        if (message.model === this.model && message.res_id === this.res_id) {
            this.msg_ids.unshift(message.id);
            this.fetch_and_render_thread(this.msg_ids);
        }
    },

    on_update_message: function (message) {
        if (message.model === this.model && message.res_id === this.res_id) {
            this.fetch_and_render_thread(this.msg_ids);
        }
    },

    on_channel_redirect: function (channel_id) {
        var self = this;
        var def = chat_manager.join_channel(channel_id);
        $.when(def).then(function () {
            // Execute Discuss client action with 'channel' as default channel
            self.trigger_up('do_action', {
                action: 'mail.mail_channel_action_client_chat',
                options: { active_id: channel_id },
            });
        });
    },

    on_redirect: function (res_model, res_id) {
        this.trigger_up('do_action', {
            action: {
                type:'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_model: res_model,
                views: [[false, 'form']],
                res_id: res_id,
            },
        });
    },

    on_followers_update: function (followers) {
        this.mention_suggestions = [];
        var self = this;
        var prefetched_partners = chat_manager.get_mention_partner_suggestions();
        var follower_suggestions = [];
        _.each(followers, function (follower) {
            if (follower.res_model === 'res.partner') {
                follower_suggestions.push({
                    id: follower.res_id,
                    name: follower.name,
                    email: follower.email,
                });
            }
        });
        if (follower_suggestions.length) {
            this.mention_suggestions.push(follower_suggestions);
        }
        _.each(prefetched_partners, function (partners) {
            self.mention_suggestions.push(_.filter(partners, function (partner) {
                return !_.findWhere(follower_suggestions, { id: partner.id });
            }));
        });
    },

    load_more_messages: function () {
        this.fetch_and_render_thread(this.msg_ids, {force_fetch: true});
    },

    render: function () {
        return this.fetch_and_render_thread(this.msg_ids);
    },
    refresh_followers: function () {
        this.trigger_up('reload');
    },
    // composer toggle
    on_open_composer_new_message: function () {
        var self = this;
        if (!this.suggested_partners_def) {
            this.suggested_partners_def = $.Deferred();
            this.trigger_up('perform_model_rpc', {
                model: this.model,
                method: 'message_get_suggested_recipients',
                args: [[this.context.default_res_id], this.context],
                on_success: function (suggested_recipients) {
                    var suggested_partners = [];
                    var thread_recipients = suggested_recipients[self.context.default_res_id];
                    _.each(thread_recipients, function (recipient) {
                        var parsed_email = utils.parse_email(recipient[1]);
                        suggested_partners.push({
                            checked: true,
                            partner_id: recipient[0],
                            full_name: recipient[1],
                            name: parsed_email[0],
                            email_address: parsed_email[1],
                            reason: recipient[2],
                        });
                    });
                    self.suggested_partners_def.resolve(suggested_partners);
                },
            });
        }
        this.suggested_partners_def.then(function (suggested_partners) {
            self.open_composer({ is_log: false, suggested_partners: suggested_partners });
        });
    },
    on_open_composer_log_note: function () {
        this.open_composer({is_log: true});
    },
    open_composer: function (options) {
        var self = this;
        var old_composer = this.composer;
        // create the new composer
        this.composer = new ChatterComposer(this, this.model, options.suggested_partners || [], {
            commands_enabled: false,
            context: this.context,
            input_min_height: 50,
            input_max_height: Number.MAX_VALUE, // no max_height limit for the chatter
            input_baseline: 14,
            is_log: options && options.is_log,
            record_name: this.record_name,
            default_body: old_composer && old_composer.$input && old_composer.$input.val(),
            default_mention_selections: old_composer && old_composer.mention_get_listener_selections(),
        });
        this.composer.on('input_focused', this, function () {
            this.composer.mention_set_prefetched_partners(this.mention_suggestions || []);
        });
        this.composer.insertBefore(this.$('.o_mail_thread')).then(function () {
            // destroy existing composer
            if (old_composer) {
                old_composer.destroy();
            }
            if (!config.device.touch) {
                self.composer.focus();
            }
            self.composer.on('post_message', self, self.on_post_message);
            self.composer.on('need_refresh', self, self.refresh_followers);
            self.composer.on('close_composer', null, self.close_composer.bind(self, true));
        });
        this.mute_new_message_button(true);
    },
    close_composer: function (force) {
        if (this.composer && (this.composer.is_empty() || force)) {
            this.composer.do_hide();
            this.composer.$input.val('');
            this.mute_new_message_button(false);
        }
    },
    mute_new_message_button: function (mute) {
        if (mute) {
            this.$('.o_chatter_button_new_message').removeClass('btn-primary').addClass('btn-default');
        } else if (!mute) {
            this.$('.o_chatter_button_new_message').removeClass('btn-default').addClass('btn-primary');
        }
    },

    destroy: function () {
        chat_manager.remove_chatter_messages(this.model);
        this._super.apply(this, arguments);
    },
});

field_registry.add('mail_thread', Chatter);

});

odoo.define('web_studio.FormEditor', function (require) {
"use strict";

var core = require('web.core');

var FormRenderer = require('web.FormRenderer');
var FormEditorHook = require('web_studio.FormEditorHook');

var _t = core._t;

var FormEditor =  FormRenderer.extend({
    className: FormRenderer.prototype.className + ' o_web_studio_form_view_editor',
    events: _.extend({}, FormRenderer.prototype.events, {
        'click .o_web_studio_add_chatter': function(event) {
            // prevent multiple click
            $(event.currentTarget).css('pointer-events', 'none');
            this.trigger_up('view_change', {
                structure: 'chatter',
                remove_follower_ids: this.has_follower_field,
                remove_message_ids: this.has_message_field,
            });
        },
        'click .o_web_studio_buttonbox_hook': function() {
            this.trigger_up('view_change', {
                structure: 'buttonbox',
            });
        }
    }),

    init: function(parent, arch, fields, state, widgets_registry, options) {
        this._super.apply(this, arguments);
        this.show_invisible = options && options.show_invisible;
        this.chatter_allowed = options.chatter_allowed;
        this.silent = false;
    },
    _render: function() {
        var self = this;
        this.has_chatter = false;
        this.has_follower_field = false;
        this.has_message_field = false;

        return this._super.apply(this, arguments).then(function() {
            // Add chatter hook
            if (!self.has_chatter && self.chatter_allowed) {
                var $chatter_hook = $('<div>')
                    .addClass('o_web_studio_add_chatter')
                    .append($('<span>', {
                        text: _t('Add Chatter Widget'),
                    }));
                $chatter_hook.insertAfter(self.$('.o_form_sheet'));
            }
            // Add buttonbox hook
            if (!self.$('.oe_button_box').length) {
                var $buttonbox_hook = $('<div>')
                    .addClass('o_web_studio_buttonbox_hook oe_button_box')
                    .append($('<span>', {
                        text: _t('Add a Button Box'),
                    }));
                self.$('.o_form_sheet').prepend($buttonbox_hook);
            }
        });
    },
    _render_node: function(node) {
        var $el = this._super.apply(this, arguments);
        if (node.tag === 'div' && node.attrs.class === 'oe_chatter') {
            this.has_chatter = true;
            this._set_style_events($el);
            // Put a div in overlay preventing all clicks chatter's elements
            $el.append($('<div>', { 'class': 'o_web_studio_overlay' }));
            $el.on('click', this.trigger_up.bind(this, 'chatter_clicked'));
        }
        return $el;
    },
    _render_tag_field: function(node) {
        var $el = this._super.apply(this, arguments);
        this._process_field(node, $el);
        return $el;
    },
    _render_tag_group: function(node) {
        var $result = this._super.apply(this, arguments);
        // Add hook after this group
        var studioNewLine = new FormEditorHook(this, node);
        studioNewLine.appendTo($('<div>')); // start the widget
        return $result.add(studioNewLine.$el);
    },
    _render_inner_group: function(node) {
        var self = this;
        var $result = this._super.apply(this, arguments);
        // Add click event to see group properties in sidebar
        $result.click(function(event) {
            event.stopPropagation();
            self.trigger_up('group_clicked', {node: node});
        });
        this._set_style_events($result);
        // Add hook only for groups that have not yet content.
        if (!node.children.length) {
            var formEditorHook = new FormEditorHook(this, node, 'inside');
            formEditorHook.appendTo($result);
            this._set_style_events($result);
        }
        return $result;
    },
    _render_adding_content_line: function (node) {
        var studioNewLine = new FormEditorHook(this, node);
        studioNewLine.appendTo($('<div>')); // start the widget
        return studioNewLine.$el;
    },
    _render_inner_field: function(node) {
        var $result = this._super.apply(this, arguments);

        // Add hook only if field is visible
        if (!$result.find('.o_form_field').is('.o_form_invisible')) {
            $result = $result.add(this._render_adding_content_line(node));
        }

        this._process_field(node, $result.find('.o_td_label').parent());
        return $result;
    },
    _render_tag_notebook: function(node) {
        var self = this;
        var $result = this._super.apply(this, arguments);

        var $addTag = $('<li>').append('<a href="#"><i class="fa fa-plus-square" aria-hidden="true"></a></i>');
        $addTag.click(function(event) {
            event.preventDefault();
            event.stopPropagation();
            self.trigger_up('view_change', {
                type: 'add',
                structure: 'page',
                node: node.children[node.children.length - 1], // Get last page in this notebook
            });
        });

        $result.find('ul.nav-tabs').append($addTag);
        return $result;
    },
    _render_tab_header: function(page) {
        var self = this;
        var $result = this._super.apply(this, arguments);
        $result.click(function(event) {
            event.preventDefault();
            if (!self.silent) {
                self.trigger_up('page_clicked', {node: page});
            }
        });
        this._set_style_events($result);
        return $result;
    },
    _render_tab_page: function(page) {
        var $result = this._super.apply(this, arguments);
        // Add hook only for pages that have not yet content.
        if (!$result.children().length) {
            var formEditorHook = new FormEditorHook(this, page, 'inside');
            formEditorHook.appendTo($result);
        }
        return $result;
    },
    _render_button_box: function() {
        var self = this;
        var $buttonbox = this._super.apply(this, arguments);
        var $buttonhook = $('<button>').addClass('btn btn-sm oe_stat_button o_web_studio_button_hook');
        $buttonhook.click(function(event) {
            event.preventDefault();

            self.trigger_up('view_change', {
                type: 'add',
                structure: 'button',
            });
        });

        $buttonhook.prependTo($buttonbox);
        return $buttonbox;
    },
    _render_stat_button: function(node) {
        var self = this;
        var $button = this._super.apply(this, arguments);
        $button.click(function(ev) {
            if (! $(ev.target).closest('.o_form_field').length) {
                // click on the button and not on the field inside this button
                self.trigger_up('button_clicked', {node: node});
            }
        });
        this._set_style_events($button);
        return $button;
    },
    _handle_attributes: function($el) {
        this._super.apply(this, arguments);
        if (this.show_invisible && $el.hasClass('o_form_invisible')) {
            $el.removeClass('o_form_invisible').addClass('o_web_studio_show_invisible');
        }
    },
    _process_field: function(node, $el) {
        var self = this;
        // detect presence of mail fields
        if (node.attrs.name === "message_ids") {
            this.has_message_field = true;
        } else if (node.attrs.name === "message_follower_ids") {
            this.has_follower_field = true;
        } else {
            // bind handler on field clicked to edit field's attributes
            $el.click(function(event) {
                event.preventDefault();
                event.stopPropagation();
                self.trigger_up('field_clicked', {node: node});
            });
            this._set_style_events($el);
        }
    },
    _set_style_events: function($el) {
        var self = this;
        $el.click(function() {
            self._reset_clicked_style();
            $(this).addClass('o_clicked');
        })
        .mouseover(function(event) {
            $(this).addClass('o_hovered');
            event.stopPropagation();
        })
        .mouseout(function(event) {
            $(this).removeClass('o_hovered');
            event.stopPropagation();
        });
    },
    _reset_clicked_style: function() {
        this.$('.o_clicked').removeClass('o_clicked');
    },
    set_local_state: function() {
        this.silent = true;
        this._super.apply(this, arguments);
        this._reset_clicked_style();
        this.silent = false;
    }
});

return FormEditor;

});

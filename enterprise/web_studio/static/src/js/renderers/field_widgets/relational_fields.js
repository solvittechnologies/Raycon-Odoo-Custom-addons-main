odoo.define('web.relational_fields', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var ControlPanel = require('web.ControlPanel');
var core = require('web.core');
var data = require('web.data');
var field_utils = require('web.field_utils');
var common = require('web.form_common');
var Dialog = require('web.Dialog');
var Pager = require('web.Pager');
var pyeval = require('web.pyeval');
var utils = require('web.utils');
var ReadonlyListRenderer = require('web.ReadonlyListRenderer');
var EditableListRenderer = require('web.EditableListRenderer');
var KanbanRenderer = require('web.KanbanRenderer');

var _t = core._t;
var qweb = core.qweb;


var AbstractRelationalField = AbstractField.extend({
    init: function(parent, name, record) {
        this._super.apply(this, arguments);
        // 'domain' and 'context' that should be used by the field widget. It
        // can come from the attrs, and is mostly useful for rpcs
        this.domain = this.field.__attrs.domain || this.field.domain || [];
        this.context = this.field.__attrs.context || this.field.context || {};

        // todo: remove this
        this.record = record;
    },
    _reset: function (record) {
        this.record = record;
        this._super.apply(this, arguments);
    },
});

var M2ODialog = Dialog.extend({
    template: "M2ODialog",
    init: function(parent, name, value) {
        this.name = name;
        this.value = value;
        this._super(parent, {
            title: _.str.sprintf(_t("Create a %s"), this.name),
            size: 'medium',
            buttons: [{
                text: _t('Create'),
                classes: 'btn-primary',
                click: function () {
                    if (this.$("input").val() !== ''){
                        this.trigger_up('quick_create', { value: this.$('input').val() });
                        this.close();
                    } else {
                        this.$("input").focus();
                    }
                },
            }, {
                text: _t('Create and edit'),
                classes: 'btn-primary',
                close: true,
                click: function () {
                    this.trigger_up('search_create_popup', {
                        view_type: 'form',
                        value: this.$('input').val(),
                    });
                },
            }, {
                text: _t('Cancel'),
                close: true,
            }],
        });
    },
    start: function() {
        this.$("p").text(_.str.sprintf(_t("You are creating a new %s, are you sure it does not exist yet?"), this.name));
        this.$("input").val(this.value);
    },
});

var FieldX2Many = AbstractRelationalField.extend({
    tagName: 'div',
    custom_events: _.extend({}, AbstractField.prototype.custom_events, {
        open_record: function(event) {
            event.data = _.extend({}, event.data, {
                context: data.build_context(this.record, this.context),
                db_id: this.state.id,
                domain: data.build_context(this.record, this.domain),
                form_view: this.field.views && this.field.views.form,
                on_success: this.update_state.bind(this),
                readonly: this.mode === 'readonly',
                string: this.string,
            });
            event.stopped = false;
        },
    }),
    init: function(parent, name, record, options) {
        this._super.apply(this, arguments);
        this.state = this.record.relational_data[this.name];
        this.view = this.field.views.tree || this.field.views.kanban;
        this.widgets_registry = options && options.widgets_registry;
        this.operations = [];
    },
    start: function() {
        return this._render_control_panel().then(this._super.bind(this));
    },
    update_state: function(data) {
        this.state = data;
        this.render();
    },
    _reset: function () {
        this._super.apply(this, arguments);
        this.state = this.record.relational_data[this.name];
    },
    render: function() {
        if (!this.view) {
            return this._super();
        }
        if (this.renderer) {
            this.renderer.update(this.state);
            this.pager.update_state({ size: this.state.count });
            return;
        }
        var arch = this.view.arch;
        var fields = this.view.fields;
        if (arch.tag === 'tree') {
            var Renderer = this.mode === 'readonly' ? ReadonlyListRenderer : EditableListRenderer;
            this.renderer = new Renderer(this, arch, fields, this.state, this.widgets_registry);
        }
        if (arch.tag === 'kanban') {
            var record_options = {
                editable: false,
                deletable: false,
                model: this.state.model, // required by includes of KanbanRecord
                read_only_mode: this.mode === 'readonly',
            };
            this.renderer = new KanbanRenderer(this, arch, fields, this.state, this.widgets_registry, record_options);
        }
        return this.renderer ? this.renderer.appendTo(this.$el) : this._super();
    },
    is_set: function() {
        return !!this.value.length;
    },
    _render_control_panel: function() {
        if (!this.view) {
            return $.when();
        }
        var self = this;
        var defs = [];
        this.control_panel = new ControlPanel(this, "X2ManyControlPanel");
        this.pager = new Pager(this, this.state.count, this.state.offset + 1, this.state.limit, {
            single_page_hidden: true,
        });
        this.pager.on('pager_changed', this, function (new_state) {
            this.trigger_up('load', {
                id: this.state.id,
                limit: new_state.limit,
                offset: new_state.current_min - 1,
                on_success: this.update_state.bind(this),
            });
        });
        if (this.mode === 'edit' && this.view.arch.tag === 'kanban') {
            // TODO: remove this and update the kanbanview.buttons template
            var widget = _.extend({}, this, {options: this.node_options});
            this.$buttons = $(qweb.render('KanbanView.buttons', {widget: widget}));
            this.$buttons.on('click', 'button.o-kanban-button-new', this._create_record.bind(this));
        }
        defs.push(this.pager.appendTo($('<div>'))); // start the pager
        defs.push(this.control_panel.prependTo(this.$el));
        return $.when.apply($, defs).then(function() {
            self.control_panel.update({
                cp_content: {
                    $buttons: self.$buttons,
                    $pager: self.pager.$el,
                }
            });
        });
    },
    _create_record: function(event) {
        // to implement
    },
});

var FieldOne2Many = FieldX2Many.extend({
    className: 'o_form_field_one2many',
    custom_events: _.extend({}, FieldX2Many.prototype.custom_events, {
        kanban_record_delete: function(event) {
            this.set_value(['DELETE', event.data.record.id]);
        },
    }),
    _create_record: function() {
        var self = this;
        new common.FormViewDialog(this, {
            res_model: this.field.relation,
            domain: data.build_domain(this.record, this.domain),
            context: data.build_context(this.record, this.context),
            title: _t('Create: ') + this.string,
            initial_view: 'form',
            alternative_form_view: this.field.views ? this.field.views.form : undefined,
            create_function: function(data) {
                self.set_value(['CREATE', data]);
                return $.when(data);
            },
            read_function: function(data) {
                return $.when([data]);
            },
            child_name: this.name,
            form_view_options: {'not_interactible_on_create': true},
        }).open();
    },
});

var FieldMany2Many = FieldX2Many.extend({
    className: 'o_form_field_many2many',
    custom_events: _.extend({}, FieldX2Many.prototype.custom_events, {
        kanban_record_delete: function(event) {
            this.set_value(_.without(this.value, event.data.record.id));
        },
    }),
    init: function() {
        this._super.apply(this, arguments);
        this.node_options = _.defaults(this.node_options, {
            create_text: _t('Add'),
        });
    },
    _create_record: function() {
        var self = this;
        new common.SelectCreateDialog(this, {
            res_model: this.field.relation,
            domain: new data.CompoundDomain(data.build_domain(this.record, this.domain), ["!", ["id", "in", this.value]]),
            context: data.build_context(this.record, this.context),
            title: _t("Add: ") + this.string,
            on_selected: function(res_ids) {
                self.set_value(self.value.concat(res_ids));
            }
        }).open();
    },
});

var FieldMany2One = AbstractRelationalField.extend({
    custom_events: {
        'quick_create': function (event) {
            this.quick_create(event.data.value);
        },
        'search_create_popup': function (event) {
            var data = event.data;
            this.search_create_popup(data.view_type, false, this._create_context(data.value));
        },
    },
    events: _.extend({}, AbstractField.prototype.events, {
        'click .o_form_input': function () {
            if (this.$input.autocomplete("widget").is(":visible")) {
                this.$input.autocomplete("close");
            } else {
                this.$input.autocomplete("search", "");
            }
        },
        'focusout .o_form_input': function () {
            if (this.can_create && this.floating) {
                new M2ODialog(this, this.string, this.$input.val()).open();
            }
        },
        'keyup .o_form_input': function () {
            if (this.$input.val() === "") {
                this.reinitialize(false);
            } else if (this.m2o_value !== this.$input.val()) {
                this.floating = true;
                this.update_external_button();
            }
        },
        'click .o_external_button': function () {
            if (!this.value) {
                this.focus();
                return;
            }
            var self = this;
            var context = data.build_context(this.record, this.context);
            this.trigger_up('perform_model_rpc', {
                method: 'get_formview_id',
                model: this.field.relation,
                args: [[this.value], context.eval()],
                on_success: function (view_id) {
                    var pop = new common.FormViewDialog(this, {
                        res_model: self.field.relation,
                        res_id: self.value,
                        context: context,
                        title: _t("Open: ") + self.string,
                        view_id: view_id,
                        readonly: !self.can_write,
                    }).open();
                    pop.on('write_completed', self, function () {
                        self.trigger_up('name_get', {
                            model: self.field.relation,
                            ids: [self.value],
                            on_success: function (value) {
                                self.reinitialize(value[0][0], value[0][1]);
                                self.focus();
                            }
                        });
                    });
                },
            });
        },
    }),
    template: 'NewFieldMany2One',

    init: function () {
        this._super.apply(this, arguments);
        this.limit = 7;
        this.orderer = new utils.DropMisordered();
        this.can_create = 'can_create' in this.field.__attrs ? this.field.__attrs.can_create : true;
        this.can_write = 'can_write' in this.field.__attrs ? this.field.__attrs.can_write : true;
        this.node_options = _.defaults(this.node_options, {
            quick_create: true,
        });
        this.m2o_value = field_utils.format_many2one(this.value, this.field, this.record_data, {
            relational_data: this.record.relational_data,
        });
    },

    start: function () {
        this.floating = false;
        this.$input = this.$('.o_form_input');
        this.$external_button = this.$('.o_external_button');
        return this._super.apply(this, arguments);
    },
    _reset: function () {
        this._super.apply(this, arguments);
        this.m2o_value = field_utils.format_many2one(this.value, this.field, this.record_data, {
            relational_data: this.record.relational_data,
        });
    },
    reinitialize: function (value, m2o_value) {
        this.m2o_value = m2o_value || '';
        this.floating = false;
        this.set_value(value);
        this.render();
    },
    render_edit: function () {
        this.$input.val(this.m2o_value);
        if (!this.autocomplete_bound) {
            this.bind_autocomplete();
        }
        this.update_external_button();
    },
    bind_autocomplete: function () {
        var self = this;
        this.$input.autocomplete({
            source: function (req, resp) {
                self.search(req.term).then(function (result) {
                    resp(result);
                });
            },
            select: function (event, ui) {
                var item = ui.item;
                self.floating = false;
                if (item.id) {
                    self.reinitialize(item.id, item.name);
                } else if (item.action) {
                    item.action();
                }
                return false;
            },
            focus: function (event) {
                event.preventDefault(); // don't automatically select values on focus
            },
            autoFocus: true,
            html: true,
            minLength: 0,
            delay: 200,
        });
        this.$input.autocomplete("option", "position", { my : "left top", at: "left bottom" });
        this.autocomplete_bound = true;
    },
    search: function (search_val) {
        var self = this;
        var def = $.Deferred();
        this.orderer.add(def);

        var exclusion_domain = [];
        var blacklisted_ids = this.get_search_blacklist();
        if (blacklisted_ids.length > 0) {
            exclusion_domain.push(['id', 'not in', blacklisted_ids]);
        }
        var domain = new data.CompoundDomain(data.build_domain(this.record, this.domain), exclusion_domain);
        this.trigger_up('name_search', {
            model: this.field.relation,
            search_val: search_val,
            domain: pyeval.eval('domain', domain),
            operator: 'ilike',
            limit: this.limit + 1,
            on_success: function (result) {
                // possible selections for the m2o
                var values = _.map(result, function(x) {
                    x[1] = x[1].split("\n")[0];
                    return {
                        label: _.str.escapeHTML(x[1].trim()) || data.noDisplayContent,
                        value: x[1],
                        name: x[1],
                        id: x[0],
                    };
                });

                // search more... if more results than limit
                if (values.length > self.limit) {
                    values = values.slice(0, self.limit);
                    values.push({
                        label: _t("Search More..."),
                        action: function() {
                            self.trigger_up('name_search', {
                                model: self.field.relation,
                                search_val: search_val,
                                domain: pyeval.eval('domain', domain),
                                operator: 'ilike',
                                limit: 160,
                                on_success: self.search_create_popup.bind(self, "search"),
                            });
                        },
                        classname: 'o_m2o_dropdown_option',
                    });
                }
                var create_enabled = self.can_create && !self.node_options.no_create;
                // quick create
                var raw_result = _.map(result, function(x) { return x[1]; });
                if (create_enabled && !self.node_options.no_quick_create &&
                    search_val.length > 0 && !_.contains(raw_result, search_val)) {
                    values.push({
                        label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                            $('<span />').text(search_val).html()),
                        action: self.quick_create.bind(self, search_val),
                        classname: 'o_m2o_dropdown_option'
                    });
                }
                // create and edit ...
                if (create_enabled && !self.node_options.no_create_edit) {
                    values.push({
                        label: _t("Create and Edit..."),
                        action: self.search_create_popup.bind(self, "form", false, self._create_context(search_val)),
                        classname: 'o_m2o_dropdown_option',
                    });
                } else if (values.length === 0) {
                    values.push({
                        label: _t("No results to show..."),
                    });
                }

                def.resolve(values);
            },
        });

        return def;
    },
    get_search_blacklist: function() {
        return [];
    },
    quick_create: function(name) {
        var self = this;
        var slow_create = this.search_create_popup.bind(this, "form", false, this._create_context(name));
        if (this.node_options.quick_create) {
            this.trigger_up('name_create', {
                model: this.field.relation,
                name: name,
                context: data.build_context(this.record, this.context),
                on_success: function (result) {
                    if (self.mode === "edit") {
                        self.reinitialize(result[0], result[1]);
                    }
                },
                on_fail: slow_create,
            });
        } else {
            slow_create();
        }
    },
    // all search/create popup handling
    search_create_popup: function(view, ids, context) {
        var self = this;
        new common.SelectCreateDialog(this, _.extend({}, this.node_options, {
            res_model: this.field.relation,
            domain: data.build_domain(this.record, this.domain),
            context: new data.CompoundContext(data.build_context(this.record, this.context), context || {}),
            title: (view === 'search' ? _t("Search: ") : _t("Create: ")) + this.string,
            initial_ids: ids ? _.map(ids, function(x) { return x[0]; }) : undefined,
            initial_view: view,
            disable_multiple_selection: true,
            on_selected: function(element_ids) {
                self.add_id(element_ids[0]);
                self.focus();
            }
        })).open();
    },
    _create_context: function(name) {
        var tmp = {};
        var field = this.node_options.create_name_field;
        if (field === undefined)
            field = "name";
        if (field !== false && name && this.node_options.quick_create !== false)
            tmp["default_" + field] = name;
        return tmp;
    },

    update_external_button: function () {
        var has_external_button = !this.node_options.no_open && !this.floating && this.is_set();
        this.$external_button.toggle(has_external_button);
        this.$el.toggleClass('o_with_button', has_external_button);
    },
    add_id: function (id) {
        var self = this;
        this.trigger_up('name_get', {
            model: this.field.relation,
            ids: [id],
            on_success: function (value) {
                self.reinitialize(value[0][0], value[0][1]);
            },
        });
    },
    focus: function () {
        if (this.mode === "edit") {
            this.$input.focus();
        }
    },
    activate: function() {
        this.$input.focus();
        setTimeout(this.$input.select.bind(this.$input), 0);
    },
});

var ListFieldMany2One = FieldMany2One.extend({
    render_readonly: function() {
        this.$el.empty().html(this.m2o_value);
    },
});

var FormFieldMany2One = FieldMany2One.extend({
    events: _.extend({}, FieldMany2One.prototype.events, {
        'click': function(event) {
            if (this.mode === 'readonly' && !this.node_options.no_open) {
                event.preventDefault();
                var context = data.build_context(this.record, this.context);
                this.trigger_up('perform_model_rpc', {
                    method: 'get_formview_action',
                    model: this.field.relation,
                    args: [[this.value], context.eval()],
                    on_success: function (action) {
                        this.trigger_up('do_action', {action: action});
                    },
                });
            }
        },
    }),
    render_readonly: function() {
        var value = _.escape((this.m2o_value || "").trim()).split("\n").join("<br/>");
        this.$el.html(value);
        if (!this.node_options.no_open) {
            this.$el.attr('href', '#');
            this.$el.addClass('o_form_uri');
        }
    },
});

var FieldMany2ManyTags = AbstractRelationalField.extend({
    tag_template: "FieldMany2ManyTag",
    className: "o_form_field o_form_field_many2manytags",
    custom_events: {
        field_changed: function (event) {
            if (event.target === this) {
                event.stopped = false;
                return;
            }
            var new_value = event.data.value;
            if (new_value) {
                this.add_id(new_value);
                this.many2one.reinitialize(false);
            }
        },
        move_next: function (event) {
            // Intercept event triggered up by the many2one, to prevent triggering it twice
            if (event.target === this) {
                event.stopped = false;
                return;
            }
        }
    },
    events: _.extend({}, AbstractField.prototype.events, {
        'click .o_delete': function (event) {
            this.remove_id($(event.target).parent().data('id'));
        },
        'keydown .o_form_field_many2one input': function (event) {
            if($(event.target).val() === "" && event.which === $.ui.keyCode.BACKSPACE) {
                var $badges = this.$('.badge');
                if($badges.length) {
                    this.remove_id($badges.last().data('id'));
                }
            }
        },
    }),
    replace_element: true,

    init: function () {
        this._super.apply(this, arguments);
        this.m2m_values = this.record.relational_data[this.name] || [];
    },
    render_edit: function () {
        var self = this;
        this.render_tags();
        this.many2one = new FieldMany2One(this, this.name, this.record, {
            id_for_label: this.id_for_label,
            mode: 'edit',
        });
        this.many2one.value = false; // to prevent the M2O to take the value of the M2M
        this.many2one.m2o_value = ''; // to prevent the M2O to take the relational values of the M2M

        this.many2one.node_options.no_open = true;
        this.many2one.get_search_blacklist = function () {
            return self.value;
        };
        this.many2one.appendTo(this.$el);
    },
    render_readonly: function () {
        this.render_tags();
    },
    render_tags: function () {
        var self = this;
        var data = _.map(this.value, function(id) {
            return _.findWhere(self.m2m_values, {id: id});
        });
        this.$el.html(qweb.render(this.tag_template, {
            elements: data,
            readonly: this.mode === "readonly",
        }));
    },
    add_id: function (id) {
        if (_.contains(this.value, id)) { return; }
        var self = this;
        var def;
        if (!_.findWhere(this.m2m_values, {id: id})) {
            def = $.Deferred();
            this.trigger_up('perform_model_rpc', {
                model: this.field.relation,
                method: 'read',
                args: [[id], ['display_name', 'color']],
                on_success: function (result) {
                    self.m2m_values.push(result[0]);
                    def.resolve();
                },
            });
        }
        $.when(def).then(function () {
            self.set_value(_.uniq(self.value.concat([id])));
            self.render();
            self.many2one.focus();
        });
    },
    remove_id: function (id) {
        this.set_value(_.without(this.value, id));
        this.render();
        this.many2one.focus();
    },
    is_set: function () {
        return !!this.value.length;
    },
    activate: function () {
        this.many2one.focus();
    },
});

var FormFieldMany2ManyTags = FieldMany2ManyTags.extend({
    events: _.extend({}, FieldMany2ManyTags.prototype.events, {
        'click .badge': 'open_color_picker',
        'mousedown .o_colorpicker span': 'update_color',
        'focusout .o_colorpicker': 'close_color_picker',
    }),

    open_color_picker: function (event) {
        // FIXME: check if there is a color field on the model
        // if (this.fields.color) {
            this.$color_picker = $(qweb.render('FieldMany2ManyTag.colorpicker', {
                'widget': this,
                'tag_id': $(event.currentTarget).data('id'),
            }));

            $(event.currentTarget).append(this.$color_picker);
            this.$color_picker.dropdown('toggle');
            this.$color_picker.attr("tabindex", 1).focus();
        // }
    },
    close_color_picker: function (){
        this.$color_picker.remove();
    },
    update_color: function (event) {
        event.preventDefault();
        var self = this;
        var color = $(event.currentTarget).data('color');
        var id = $(event.currentTarget).data('id');
        var tag = self.$("span.badge[data-id='" + id + "']");
        var current_color = tag.data('color');

        if (color === current_color) { return; }

        // FIXME: trigger_up 'field_changed' instead to keep the datamodel up-to-date?
        this.trigger_up('perform_model_rpc', {
            model: this.field.relation,
            method: 'write',
            args: [id, {'color': color}],
            on_success: function () {
                tag.removeClass('o_tag_color_' + current_color);
                tag.data('color', color);
                tag.addClass('o_tag_color_' + color);
            }
        });
    },
});

var FieldMany2ManyCheckBoxes = AbstractRelationalField.extend({
    template: 'NewFieldMany2ManyCheckBoxes',
    events: _.extend({}, AbstractRelationalField.prototype.events, {
        change: function () {
            var value = _.map(this.$('input:checked'), function (input) {
                return $(input).data("record-id");
            });
            this.set_value(value);
        },
    }),
    init: function () {
        this._super.apply(this, arguments);
        this.m2m_values = this.field.__many2manys_information;
    },
    render: function () {
        var self = this;
        this._super.apply(this, arguments);
        _.each(this.value, function (id) {
            self.$('input[data-record-id="' + id + '"]').prop('checked', true);
        });
    },
    render_readonly: function () {
        this.$("input").prop("disabled", true);
    },
    is_set: function () {
        return true;
    },
});

return {
    FieldMany2Many: FieldMany2Many,
    FieldMany2ManyCheckBoxes: FieldMany2ManyCheckBoxes,
    FieldMany2ManyTags: FieldMany2ManyTags,
    FormFieldMany2ManyTags: FormFieldMany2ManyTags,
    FieldMany2One: FieldMany2One,
    FormFieldMany2One: FormFieldMany2One,
    ListFieldMany2One: ListFieldMany2One,
    FieldOne2Many: FieldOne2Many,
};

});

odoo.define('web.basic_fields', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var crash_manager = require('web.crash_manager');
var datepicker = require('web.datepicker');
var field_utils = require('web.field_utils');
var framework = require('web.framework');
var session = require('web.session');
var utils = require('web.utils');
var dom_utils = require('web.dom_utils');
var ProgressBar = require('web.ProgressBar');

var qweb = core.qweb;
var _t = core._t;


var InputField = AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'input': function() {
            this.set_value(this.$el.val());
        },
    }),

    // we want the view to aggregate the keypresses before applying the onchange
    apply_onchange_immediately: false,

    init: function() {
        this._super.apply(this, arguments);
        if (this.mode === 'edit') {
            this.tagName = 'input';
        }
    },
    render_edit: function() {
        this.$el.addClass('o_form_input');
        this.$el.attr('type', 'text');
        if (this.field.__attrs.placeholder) {
            this.$el.attr('placeholder', this.field.__attrs.placeholder);
        }
        this.$el.attr('id', this.id_for_label);
        this.$el.val(this.format_value(this.value));
    },
    render_readonly: function() {
        this.$el.empty().html(this.format_value(this.value));
    },
    activate: function() {
        this.$el.focus();
        setTimeout(this.$el.select.bind(this.$el), 0);
    },
    on_keydown: function(event) {
        var input = this.$el[0];
        var is_not_selecting;
        switch (event.which) {
            case $.ui.keyCode.DOWN:
                this.trigger_up('move_down');
                break;
            case $.ui.keyCode.UP:
                this.trigger_up('move_up');
                break;
            case $.ui.keyCode.LEFT:
                is_not_selecting = input.selectionEnd === input.selectionStart;
                if (is_not_selecting && input.selectionStart === 0) {
                    this.trigger_up('move_left');
                }
                break;
            case $.ui.keyCode.RIGHT:
                is_not_selecting = input.selectionEnd === input.selectionStart;
                if (is_not_selecting && input.selectionEnd === input.value.length) {
                    this.trigger_up('move_right');
                }
                break;
            case $.ui.keyCode.ENTER:
                this.trigger_up('move_next_line');
                break;
        }
        this._super.apply(this, arguments);
    },
});

var FieldChar = InputField.extend({
    tagName: 'span',
});

var FieldDate = InputField.extend({
    className: "o_form_field_date",
    tagName: "span",
    render_edit: function() {
        var self = this;
        var datewidget = this.build_datepicker_widget();
        datewidget.on('datetime_changed', this, function() {
            this.set_value(datewidget.get_value());
        });
        return datewidget.appendTo('<div>').done(function() {
            datewidget.$el.addClass(self.$el.attr('class'));
            datewidget.$input.addClass('o_form_input');
            datewidget.$input.attr('id', self.id_for_label);
            datewidget.set_value(self.value);
            self.replaceElement(datewidget.$el);
        });
    },
    build_datepicker_widget: function() {
        return new datepicker.DateWidget(this);
    },
});

var FieldDateTime = FieldDate.extend({
    build_datepicker_widget: function() {
        return new datepicker.DateTimeWidget(this);
    },
});

var FieldMonetary = InputField.extend({
    className: 'o_list_number',
    // FieldMonetary overrides format_value to ensure that the format_monetary
    // method is used.  This allows this widget to be used with other field
    // types, such as float.
    format_value: function(value) {
        return field_utils.format_monetary(value, this.field, this.record_data, this.node_options);
    },
    is_set: function() {
        return this.value !== false;
    }
});

var FieldSelection = AbstractField.extend({
    template: 'NewFieldSelection',
    events: _.extend({}, AbstractField.prototype.events, {
        'input': function() {
            this.set_value(JSON.parse(this.$el.val()));
        },
    }),
    init: function() {
        this._super.apply(this, arguments);
        this.values = [];
        if (this.field.type === 'many2one') {
            this.values = this.field.__selection_information;
        } else {
            this.values = _.reject(this.field.selection, function (v) {
                return v[0] === false && v[1] === '';
            });
        }
        this.values = [[false, this.field.__attrs.placeholder || '']].concat(this.values);
    },
    format_value: function(value) {
        if (this.field.type === 'many2one') {
            var relational_data = {};
            relational_data[this.name] = this.values;
            var options = _.extend({}, this.node_options, {relational_data: relational_data});
            return field_utils.format_many2one(value, this.field, this.record_data, options);
        } else {
            return this._super(value);
        }
    },
    render_readonly: function() {
        this.$el.empty().html(this.format_value(this.value));
    },
    render_edit: function() {
        this.$el.empty();
        for (var i = 0 ; i < this.values.length ; i++) {
            this.$el.append($('<option/>', {
                value: JSON.stringify(this.values[i][0]),
                html: this.values[i][1]
            }));
        }
        this.$el.val(JSON.stringify(this.parse_value(this.value)));
    },
});

var FieldRadio = FieldSelection.extend({
    template: 'NewFieldRadio',
    events: _.extend({}, AbstractField.prototype.events, {
        'click input': function(event) {
            this.set_value($(event.target).data('value'));
            this.render_edit();
        },
    }),
    init: function() {
        this._super.apply(this, arguments);
        if (this.field.type === 'selection') {
            this.values = this.field.selection || [];
        } else if (this.field.type === 'many2one') {
            this.values = this.field.__status_information;
        }
        this.unique_id = _.uniqueId("radio");
    },
    render_edit: function() {
        this.$("input").prop("checked", false);
        this.$('input[data-value="' + this.parse_value(this.value) + '"]').prop('checked', true);
    },
    is_set: function() {
        return true;
    },
});

var FieldBoolean = AbstractField.extend({
    className: 'o_field_boolean',
    events: _.extend({}, AbstractField.prototype.events, {
        change: function() {
            this.set_value(this.$input[0].checked);
        },
        keydown: function(event) {
            switch (event.which) {
                case $.ui.keyCode.DOWN:
                    this.trigger_up('move_down');
                    break;
                case $.ui.keyCode.UP:
                    this.trigger_up('move_up');
                    break;
                case $.ui.keyCode.LEFT:
                    this.trigger_up('move_left');
                    break;
                case $.ui.keyCode.RIGHT:
                    this.trigger_up('move_right');
                    break;
                case $.ui.keyCode.TAB:
                    this.trigger_up('move_next');
                    event.preventDefault();
                    break;
                case $.ui.keyCode.ENTER:
                    this.$input.prop('checked', !this.value);
                    this.set_value(!this.value);
                    break;
            }
        },
    }),
    replace_element: true,

    render_readonly: function() {
        var $checkbox = this.format_value(this.value);
        this.$input = $checkbox.find('input');
        this.$el.append($checkbox);
    },
    render_edit: function() {
        this.render_readonly();
        this.$input.prop('disabled', false);
    },
    activate: function() {
        this.$input.focus();
        setTimeout(this.$input.select.bind(this.$input), 0);
    },
    is_set: function() {
        return true;
    },
});

var FieldInteger = InputField.extend({
    is_set: function() {
        return this.value !== false;
    },
});

var FieldFloat = InputField.extend({
    render_readonly: function() {
        if (this.field.__attrs.digits) {
            this.field.digits = py.eval(this.field.__attrs.digits);
        }
        var value = this.format_value(this.value);
        var $span = $('<span>').addClass('o_form_field o_form_field_number').text(value);
        this.$el.html($span);
    },
    is_set: function() {
        return this.value !== '';
    },
});

var FieldFloatTime = FieldFloat.extend({
    format_value: function(value) {
        var pattern = '%02d:%02d';
        if (value < 0) {
            value = Math.abs(value);
            pattern = '-' + pattern;
        }
        var hour = Math.floor(value);
        var min = Math.round((value % 1) * 60);
        if (min === 60){
            min = 0;
            hour = hour + 1;
        }
        return _.str.sprintf(pattern, hour, min);
    },
    parse_value: function(value) {
        var factor = 1;
        if (value[0] === '-') {
            value = value.slice(1);
            factor = -1;
        }
        var float_time_pair = value.split(":");
        if (float_time_pair.length !== 2) {
            return factor * field_utils.parse_float(value, this.field);
        }
        var hours = field_utils.parse_integer(float_time_pair[0]);
        var minutes = field_utils.parse_integer(float_time_pair[1]);
        return factor * (hours + (minutes / 60));
    },
});

var FieldText = AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'input': function() {
            this.set_value(this.$el.val());
        },
    }),
    init: function() {
        this._super.apply(this, arguments);
        if (this.mode === 'edit') {
            this.tagName = 'textarea';
        }
    },
    start: function() {
        this.$el.addClass('o_list_text');
        this.$el.attr('id', this.id_for_label);
        return this._super();
    },
    render_readonly: function() {
        this.$el.empty().text(this.format_value(this.value));
        this.$el.addClass('o_form_textarea');
    },
    render_edit: function() {
        if (this.field.__attrs.placeholder) {
            this.$el.attr('placeholder', this.field.__attrs.placeholder);
        }
        this.$el.val(this.format_value(this.value));
        dom_utils.autoresize(this.$el, {parent: this});
        this.$el = this.$el.add(this.$el.siblings());
    }
});

var FieldHtml = InputField.extend({
    text_to_html: function (text) {
        var value = text || "";
        if (value.match(/^\s*$/)) {
            value = '<p><br/></p>';
        } else {
            value = "<p>"+value.split(/<br\/?>/).join("<br/></p><p>")+"</p>";
            value = value.replace(/<p><\/p>/g, '').replace('<p><p>', '<p>').replace('<p><p ', '<p ').replace('</p></p>', '</p>');
        }
        return value;
    },
    render: function() {
        this.$el.html(this.text_to_html(this.value));
    },
});

// for integer fields
var HandleWidget = AbstractField.extend({
    tagName: 'span',
    className: 'o_row_handle fa fa-arrows ui-sortable-handle',
    description: "",
    render_readonly: function() {
        this.$el.empty().html(this.format_value(this.value));
    },
});

var EmailWidget = InputField.extend({
    prefix: 'mailto',
    init: function() {
        this._super.apply(this, arguments);
        this.tagName = this.mode === 'readonly' ? 'a' : 'input';
    },
    render_readonly: function() {
        this.$el.text(this.value)
            .addClass('o_form_uri o_text_overflow')
            .attr('href', this.prefix + ':' + this.value);
    }
});

var UrlWidget = InputField.extend({
    init: function() {
        this._super.apply(this, arguments);
        this.tagName = this.mode === 'readonly' ? 'a' : 'input';
    },
    render_readonly: function() {
        this.$el.text(this.value)
            .addClass('o_form_uri o_text_overflow')
            .attr('href', this.value);
    }
});

var AbstractFieldBinary = AbstractField.extend({
    events: _.extend({}, AbstractField.prototype.events, {
        'change .o_form_input_file': 'on_file_change',
        'click .o_select_file_button': function() {
            this.$('.o_form_input_file').click();
        },
        'click .o_save_file_button': 'on_save_as',
        'click .o_clear_file_button': 'on_clear',
    }),
    init: function(parent, name, record) {
        this._super.apply(this, arguments);
        this.fields = record.fields;
        this.useFileAPI = !!window.FileReader;
        this.max_upload_size = 25 * 1024 * 1024; // 25Mo
        if (!this.useFileAPI) {
            var self = this;
            this.fileupload_id = _.uniqueId('o_fileupload');
            $(window).on(this.fileupload_id, function() {
                var args = [].slice.call(arguments).slice(1);
                self.on_file_uploaded.apply(self, args);
            });
        }
    },
    destroy: function() {
        $(window).off(this.fileupload_id);
        this._super.apply(this, arguments);
    },
    on_file_change: function(e) {
        var self = this;
        var file_node = e.target;
        if ((this.useFileAPI && file_node.files.length) || (!this.useFileAPI && $(file_node).val() !== '')) {
            if (this.useFileAPI) {
                var file = file_node.files[0];
                if (file.size > this.max_upload_size) {
                    var msg = _t("The selected file exceed the maximum file size of %s.");
                    this.do_warn(_t("File upload"), _.str.sprintf(msg, utils.human_size(this.max_upload_size)));
                    return false;
                }
                var filereader = new FileReader();
                filereader.readAsDataURL(file);
                filereader.onloadend = function(upload) {
                    var data = upload.target.result;
                    data = data.split(',')[1];
                    self.on_file_uploaded(file.size, file.name, file.type, data);
                };
            } else {
                this.$('form.o_form_binary_form input[name=session_id]').val(this.session.session_id);
                this.$('form.o_form_binary_form').submit();
            }
            this.$('.o_form_binary_progress').show();
            this.$('button').hide();
        }
    },
    on_file_uploaded: function(size, name) {
        if (size === false) {
            this.do_warn(_t("File Upload"), _t("There was a problem while uploading your file"));
            // TODO: use crashmanager
            console.warn("Error while uploading file : ", name);
        } else {
            this.on_file_uploaded_and_valid.apply(this, arguments);
        }
        this.$('.o_form_binary_progress').hide();
        this.$('button').show();
    },
    on_file_uploaded_and_valid: function(size, name, content_type, file_base64) {
        this.set_filename(name);
        this.set_value(file_base64);
        this.render();
    },
    on_save_as: function(ev) {
        if (!this.value) {
            this.do_warn(_t("Save As..."), _t("The field is empty, there's nothing to save !"));
            ev.stopPropagation();
        } else {
            framework.blockUI();
            var c = crash_manager;
            var filename_fieldname = this.field.__attrs.filename;
            this.session.get_file({
                'url': '/web/content',
                'data': {
                    'model': this.model,
                    'id': this.res_id,
                    'field': this.name,
                    'filename_field': filename_fieldname,
                    'filename': this.record_data[filename_fieldname] || null,
                    'download': true,
                    'data': utils.is_bin_size(this.value) ? null : this.value,
                },
                'complete': framework.unblockUI,
                'error': c.rpc_error.bind(c)
            });
            ev.stopPropagation();
        }
    },
    set_filename: function(value) {
        var filename = this.field.__attrs.filename;
        if (filename && filename in this.fields) {
            this.trigger_up('update_field', { name: filename, value: value });
        }
    },
    on_clear: function() {
        this.set_filename('');
        this.set_value(false);
        this.render();
    },
});

var FieldBinaryImage = AbstractFieldBinary.extend({
    template: 'NewFieldBinaryImage',
    placeholder: "/web/static/src/img/placeholder.png",
    events: _.extend({}, AbstractFieldBinary.prototype.events, {
        'click img': function() {
            if (this.mode === "readonly") {
                this.trigger_up('bounce_edit');
            }
        },
    }),
    render: function() {
        var self = this;
        var attrs = this.field.__attrs;
        var url = this.placeholder;
        if (this.value) {
            if (!utils.is_bin_size(this.value)) {
                url = 'data:image/png;base64,' + this.value;
            } else {
                url = session.url('/web/image', {
                    model: this.model,
                    id: JSON.stringify(this.res_id),
                    field: this.node_options.preview_image || this.name,
                    // unique forces a reload of the image when the record has been updated
                    unique: (this.record_data.__last_update || '').replace(/[^0-9]/g, ''),
                });
            }
        }
        var $img = $('<img>').attr('src', url);
        $img.css({
            width: this.node_options.size ? this.node_options.size[0] : attrs.img_width || attrs.width,
            height: this.node_options.size ? this.node_options.size[1] : attrs.img_height || attrs.height,
        });
        this.$('> img').remove();
        this.$el.prepend($img);
        $img.on('error', function() {
            self.on_clear();
            $img.attr('src', self.placeholder);
            self.do_warn(_t("Image"), _t("Could not display the selected image."));
        });
    },
    is_set: function() {
        return true;
    },
});

var FieldBinaryFile = AbstractFieldBinary.extend({
    template: 'NewFieldBinaryFile',
    events: _.extend({}, AbstractFieldBinary.prototype.events, {
        'click': function(event) {
            if (this.mode === 'readonly' && this.value) {
                this.on_save_as(event);
            }
        },
        'click .o_form_input': function() { // eq[0]
            this.$('.o_form_input_file').click();
        },
    }),
    init: function() {
        this._super.apply(this, arguments);
        this.filename_value = this.record_data[this.field.__attrs.filename];
    },
    render_readonly: function() {
        this.do_toggle(!!this.value);
        if (this.value) {
            this.$el.empty().append($("<span/>").addClass('fa fa-download'));
            if (this.filename_value) {
                this.$el.append(" " + this.filename_value);
            }
        }
    },
    render_edit: function() {
        if(this.value) {
            this.$el.children().removeClass('o_hidden');
            this.$('.o_select_file_button').first().addClass('o_hidden');
            this.$('.o_form_input').eq(0).val(this.filename_value || this.value);
        } else {
            this.$el.children().addClass('o_hidden');
            this.$('.o_select_file_button').first().removeClass('o_hidden');
        }
    },
    set_filename: function(value) {
        this._super.apply(this, arguments);
        this.filename_value = value; // will be used in the re-render
        // the filename being edited but not yet saved, if the user clicks on
        // download, he'll get the file corresponding to the current value
        // stored in db, which isn't the one whose filename is displayed in the
        // input, so we disable the download button
        this.$('.o_save_file_button').prop('disabled', true);
    },
});

var PriorityWidget = AbstractField.extend({
    className: "o_priority",
    events: {
        'mouseover > a': function(e) {
            clearTimeout(this.hover_timer);
            this.$('.o_priority_star').removeClass('fa-star-o').addClass('fa-star');
            $(e.target).nextAll().removeClass('fa-star').addClass('fa-star-o');
        },
        'mouseout > a': function() {
            clearTimeout(this.hover_timer);

            var self = this;
            this.hover_timer = setTimeout(function() {
                self.render();
            }, 200);
        },
        'click > a': function(e) {
            e.preventDefault();
            e.stopPropagation();
        },
    },
    render_star: function(tag, is_full, tip) {
        return $(tag)
            .attr('title', tip)
            .addClass('o_priority_star fa')
            .toggleClass('fa-star', is_full)
            .toggleClass('fa-star-o', !is_full);
    },
    render: function() {
        var self = this;
        var value = parseInt(this.value, 10);
        this.$el.empty();
        _.each(this.field.selection.slice(1), function(choice) {
            self.$el.append(self.render_star('<a href="#">', value >= parseInt(choice[0]), choice[1]));
        });
    },
});

var KanbanStateWidget = AbstractField.extend({
    template: 'FormSelection',
    events: {
        'click a': function(e) {
            e.preventDefault();
        },
        'click li': 'set_kanban_selection'
    },
    prepare_dropdown_values: function() {
        var self = this;
        var _data = [];
        var current_stage_id = self.record_data.stage_id[0];
        var stage_data = {
            id: current_stage_id,
            legend_normal: this.record_data.legend_normal || undefined,
            legend_blocked : this.record_data.legend_blocked || undefined,
            legend_done: this.record_data.legend_done || undefined,
        };
        _.map(this.field.selection || [], function(selection_item) {
            var value = {
                'name': selection_item[0],
                'tooltip': selection_item[1],
            };
            if (selection_item[0] === 'normal') {
                value.state_name = stage_data.legend_normal ? stage_data.legend_normal : selection_item[1];
            } else if (selection_item[0] === 'done') {
                value.state_class = 'oe_kanban_status_green';
                value.state_name = stage_data.legend_done ? stage_data.legend_done : selection_item[1];
            } else {
                value.state_class = 'oe_kanban_status_red';
                value.state_name = stage_data.legend_blocked ? stage_data.legend_blocked : selection_item[1];
            }
            _data.push(value);
        });
        return _data;
    },
    render: function() {
        var self = this;
        var states = this.prepare_dropdown_values();
        // Adapt "FormSelection"
        var current_state = _.find(states, function(state) {
            return state.name === self.value;
        });
        this.$('.oe_kanban_status')
            .removeClass('oe_kanban_status_red oe_kanban_status_green')
            .addClass(current_state.state_class);

        // Render "FormSelection.Items" and move it into "FormSelection"
        var $items = $(qweb.render('FormSelection.items', {
            states: _.without(states, current_state)
        }));
        var $dropdown = this.$('.dropdown-menu');
        $dropdown.children().remove(); // remove old items
        $items.appendTo($dropdown);
    },
    set_kanban_selection: function(ev) {
        var li = $(ev.target).closest('li');
        if (li.length) {
            var value = String(li.data('value'));
            this.set_value(value);
            if (this.mode === 'edit') {
                this.render();
            }
        }
    },
});

var StatusBar = AbstractField.extend({
    template: "NewFieldStatus",
    className: 'o_statusbar_status',
    events: {
        'click li': 'on_click_stage',
        'click .o_arrow_button': 'on_click_stage',
    },
    render: function() {
        var self = this;
        this.selection_folded = [];
        this.selection_unfolded = [];
        this.visible = this.field.__attrs.statusbar_visible;
        var status_information = this.field.selection || this.field.__status_information;

        _.each(status_information.reverse(), function(info) {
            if ((info.id || info[0]) !== self.value && (info.fold || self.visible && self.visible.indexOf(info[0]) === -1)) {
                self.selection_folded.push(
                    self.field.type === 'many2one' ? [info.id, info.display_name] : info
                );
            } else {
                self.selection_unfolded.push(
                    self.field.type === 'many2one' ? [info.id, info.display_name] : info
                );
            }
        });

        // FIXME: this should use the community template and be overriden somehow by web_enterprise
        var content = qweb.render("NewFieldStatus.content.desktop", {'widget': this});
        self.$el.html(content);
    },
    // FIXME: sometimes, the statusbar should not be clickable !
    on_click_stage: function(event) {
        var $stage = $(event.currentTarget);
        var val;
        if (this.field.type === "many2one") {
            val = parseInt($stage.data("value"), 10);
        } else {
            val = $stage.data("value");
        }
        if (val) {
            this.set_value(val);
        }
    }
});

var FieldBooleanButton = AbstractField.extend({
    className: 'o_stat_info',
    render: function() {
        this.$el.empty();
        var text, hover;
        switch (this.node_options.terminology) {
            case "active":
                text = this.value ? _t("Active") : _t("Inactive");
                hover = this.value ? _t("Deactivate") : _t("Activate");
                break;
            case "archive":
                text = this.value ?  _t("Active") : _t("Archived");
                hover = this.value ? _t("Archive") : _t("Unarchive");
                break;
            case "prod_environment":
                text = this.value ?  _t("Production Environment") : _t("Test Environment");
                hover = this.value ? _t("Switch to test environment") : _t("Switch to production environment");
                break;
            default:
                text = this.value ?  _t("On") : _t("Off");
                hover = this.value ? _t("Switch Off") : _t("Switch On");
        }
        var val_color = this.value ? 'text-success' : 'text-danger';
        var hover_color = this.value ? 'text-danger' : 'text-success';
        var $val = $('<span>').addClass('o_stat_text o_not_hover ' + val_color).text(text);
        var $hover = $('<span>').addClass('o_stat_text o_hover ' + hover_color).text(hover);
        this.$el.append($val).append($hover);
    },
    is_set: function() {
        return true;
    },
});

var FieldID = InputField.extend({
    init: function() {
        this._super.apply(this, arguments);
        this.mode = 'readonly';
    },
});

var StatInfo = AbstractField.extend({
    render: function() {
        var options = {
            value: this.value || 0,
        };
        if (! this.node_options.nolabel) {
            if(this.node_options.label_field && this.record_data[this.node_options.label_field]) {
                options.text = this.record_data[this.node_options.label_field];
            } else {
                options.text = this.string;
            }
        }
        this.$el.html(qweb.render("StatInfo", options));
        this.$el.addClass('o_stat_info');
    },
    is_set: function() {
        return true;
    },
});

var FieldPercentPie = AbstractField.extend({
    template: 'FieldPercentPie',
    start: function() {
        this.$left_mask = this.$('.o_mask').first();
        this.$right_mask = this.$('.o_mask').last();
        this.$pie_value = this.$('.o_pie_value');
        return this._super();
    },
    render: function() {
        var value = this.value || 0;
        var degValue = 360*value/100;

        this.$right_mask.toggleClass('o_full', degValue >= 180);

        var leftDeg = 'rotate(' + ((degValue < 180)? 180 : degValue) + 'deg)';
        var rightDeg = 'rotate(' + ((degValue < 180)? degValue : 0) + 'deg)';
        this.$left_mask.css({transform: leftDeg, msTransform: leftDeg, mozTransform: leftDeg, webkitTransform: leftDeg});
        this.$right_mask.css({transform: rightDeg, msTransform: rightDeg, mozTransform: rightDeg, webkitTransform: rightDeg});

        this.$pie_value.html(Math.round(value) + '%');
    },
    is_set: function() {
        return true;
    },
});

var FieldProgressBar = AbstractField.extend({
    start: function() {
        if(this.progressbar) {
            this.progressbar.destroy();
        }

        this.progressbar = new ProgressBar(this, {
            readonly: this.mode === 'readonly',
            edit_on_click: true,
            value: this.value || 0,
        });

        var self = this;
        this.$el = $('<div>');
        this.progressbar.appendTo(this.$el).done(function() {
            self.progressbar.$el.addClass(self.$el.attr('class'));
            self.replaceElement(self.progressbar.$el);

            self.progressbar.on('update', self, function(update) {
                self.set_value(update.changed_value);
            });
        });
    },
    is_set: function() {
        return true;
    },
});

/**
    This widget is intended to be used on boolean fields. It toggles a button
    switching between a green bullet / gray bullet.
*/
var FieldToggleBoolean = AbstractField.extend({
    template: "toggle_button",
    events: {
        'click': 'set_toggle_button'
    },
    render: function () {
        var class_name = this.value ? 'o_toggle_button_success' : 'text-muted';
        this.$('i').attr('class', ('fa fa-circle ' + class_name));
    },
    set_toggle_button: function () {
        var toggle_value = !this.value;
        this.set_value(toggle_value);
        if (this.mode === 'edit') {
            this.render();
        }
    },
    is_set: function() {
        return true;
    },
});

return {
    EmailWidget: EmailWidget,
    FieldBinaryFile: FieldBinaryFile,
    FieldBinaryImage: FieldBinaryImage,
    FieldBoolean: FieldBoolean,
    FieldBooleanButton: FieldBooleanButton,
    FieldChar: FieldChar,
    FieldDate: FieldDate,
    FieldDateTime: FieldDateTime,
    FieldFloat: FieldFloat,
    FieldFloatTime: FieldFloatTime,
    FieldHtml: FieldHtml,
    FieldID: FieldID,
    FieldInteger: FieldInteger,
    FieldMonetary: FieldMonetary,
    FieldPercentPie: FieldPercentPie,
    FieldProgressBar: FieldProgressBar,
    FieldRadio: FieldRadio,
    FieldSelection: FieldSelection,
    FieldText: FieldText,
    FieldToggleBoolean: FieldToggleBoolean,
    HandleWidget: HandleWidget,
    InputField: InputField,
    KanbanStateWidget: KanbanStateWidget,
    PriorityWidget: PriorityWidget,
    StatInfo: StatInfo,
    StatusBar: StatusBar,
    UrlWidget: UrlWidget,
};

});

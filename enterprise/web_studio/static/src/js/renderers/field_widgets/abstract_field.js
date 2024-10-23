odoo.define('web.AbstractField', function (require) {
"use strict";

var field_utils = require('web.field_utils');
var pyeval = require('web.pyeval');
var Widget = require('web.Widget');

// This is the basic field widget used by all the views to render a field in a view.
// These field widgets are mostly common to all views, in particular form and list
// views.

// The responsabilities of a field widget are mainly:
// * render a visual representation of the current value of a field
// * that representation is either in 'readonly' or in 'edit' mode
// * notify the rest of the system when the field has been changed by
//   the user (in edit mode)

// Notes
// * the widget is not supposed to be able to switch between modes.  If another
//   mode is required, the view will take care of instantiating another widget.
// * notify the system when its value has changed and its mode is changed to 'readonly'
// * notify the system when some action has to be taken, such as opening a record
// * the Field widget should not, ever, under any circumstance, be aware of
//   its parent.  The way it communicates changes with the rest of the system is by
//   triggering events (with trigger_up).  These events bubble up and are interpreted
//   by the most appropriate parent.

// Also, in some cases, it may not be practical to have the same widget for all
// views. In that situation, you can have a 'view specific widget'.  Just register
// the widget in the registry prefixed by the view type and a dot.  So, for example,
// a form specific many2one widget should be registered as 'form.many2one'.
return Widget.extend({
    className: 'o_field_widget',
    events: {
        'keydown': 'on_keydown',
    },

    // this flag determines if the form view will apply the onchanges immediately
    // or can wait a little bit to apply them.  The main reason is that you don't
    // want to apply onchanges for each keypress in an input. Clearly, for most of the
    // other use cases, it is desired to apply onchanges as soon as possible.
    apply_onchange_immediately: true,

    init: function(parent, name, record, options) {
        this._super(parent);
        options = options || {};

        // 'name' is the field name displayed by this widget
        this.name = name;

        // the 'field' property is a description of all the various field properties,
        // such as the type, the comodel (relation), ...
        this.field = record.fields[name];

        // this property tracks the current (parsed if needed) value of the field.
        // Note that we don't use an event system anymore, using this.get('value')
        // is no longer valid.
        this.value = record.data[name];

        // record_data tracks the values for the other fields for the same record.
        // note that it is expected to be mostly a readonly property, you cannot
        // use this to try to change other fields value, this is not how it is
        // supposed to work. Also, do not use this.record_data[this.name] to get
        // the current value, this could be out of sync after a set_value.
        this.record_data = record.data;

        // the 'string' property is a human readable (and translated) description
        // of the field. Mostly useful to be displayed in various places in the
        // UI, such as tooltips or create dialogs.
        this.string = this.field.__attrs.string || this.field.string || this.name;

        // Widget can often be configured in the 'options' attribute in the
        // xml 'field' tag.  These options are saved (and evaled) in node_options
        this.node_options = pyeval.py_eval(this.field.__attrs.options || '{}');

        // local_id is the id corresponding to the current record in the model.
        // Its intended use is to be able to tag any messages going upstream,
        // so the view knows which records was changed for example.
        this.local_id = record.id;

        // this is the res_id for the record in database.  Obviously, it is
        // readonly.  Also, when the user is creating a new record, there is
        // no res_id.  When the record will be created, the field widget will
        // be destroyed (when the form view switches to readonly mode) and a new
        // widget with a res_id in mode readonly will be created.
        this.res_id = record.res_id;

        // useful mostly to trigger rpcs on the correct model
        this.model = record.model;

        // a widget can be in two modes: 'edit' or 'readonly'.  This mode should
        // never be changed, if a view changes its mode, it will destroy and
        // recreate a new field widget.
        this.mode = options.mode || "readonly";

        // this flag tracks if the widget is in a valid state, meaning that the
        // current value represented in the DOM is a value that can be parsed
        // and saved.  For example, a float field can only use a number and not
        // a string.
        this._is_valid = true;

        // the 'required' flag is basically only needed to determine if the widget
        // is in a valid state (not valid if empty and required)
        this.required = options.required || false;

        // the 'id_for_label' is the (html) id that should be set to the relevent
        // dom entity.  If done correctly, clicking on the corresponding label
        // (in form view) will focus and select the value.
        this.id_for_label = options.id_for_label;
    },
    start: function() {
        return this._super.apply(this, arguments).then(this.render.bind(this));
    },
    // this method is supposed to be called from the outside of field widgets.
    // The typical use case is when an onchange has changed the widget value.
    // It will reset the widget to the values that could have changed, then will
    // rerender the widget.
    reset: function (record) {
        this._reset(record);
        this.render();
    },
    // pure version of reset, can be overridden, called before render()
    _reset: function(record) {
        this.value = record.data[this.name];
        this.record_data = record.data;
    },
    // this method is called by the widget, to change its value and to notify
    // the outside world of its new state.  This method also validates the new
    // value.  Note that this method does not rerender the widget, it should be
    // handled by the widget itself, if necessary.
    set_value: function(value) {
        try {
            this.value = this.parse_value(value);
            this._is_valid = true;
        } catch(e) {
            this._is_valid = false;
        }
        var changes = {
            local_id: this.local_id,
            name: this.name,
            value: this.value,
            apply_onchange_immediately: this.apply_onchange_immediately,
        };
        this.trigger_up('field_changed', changes);
    },
    // main rendering function.  Override this if your widget has the same render
    // for each mode.  Also, note that this function is supposed to be idempotent:
    // the result of calling 'render' twice is the same as calling it once.
    render: function() {
        if (this.mode === 'edit') {
            this.render_edit();
        } else if (this.mode === 'readonly') {
            this.render_readonly();
        }
    },
    render_edit: function() {
        // to be implemented
    },
    render_readonly: function() {
        // to be implemented
    },
    // convert the value from the field to a string representation
    format_value: function(value) {
        var formatter = field_utils['format_' + this.field.type];
        return formatter(value, this.field, this.record_data, this.node_options);
    },
    // convert a string representation to a valid value
    parse_value: function(value) {
        return field_utils['parse_' + this.field.type](value);
    },
    // Right now, this function is only used in editable list view when the user
    // select a cell.  The corresponding widget will be activated, which in general
    // means that the input text will be focused and selected
    activate: function() {
        // to be implemented
    },
    // this method is used to determine if the field value is set to a meaningful
    // value.  This is useful to determine if a field should be displayed as empty
    is_set: function() {
        return !!this.value;
    },
    // a field widget is valid if its value is valid and if there is a value when
    // it is required.  This is checked before saving a record, by the form view.
    is_valid: function() {
        return this._is_valid && !(this.required && !this.is_set());
    },
    // might be controversial: intercept the tab key, to allow the editable list
    // view to control where the focus is.
    on_keydown: function(event) {
        if (event.which === $.ui.keyCode.TAB) {
            this.trigger_up('move_next');
            event.preventDefault();
        }
    },
});

});

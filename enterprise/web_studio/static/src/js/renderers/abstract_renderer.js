odoo.define('web.AbstractRenderer', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var qweb = core.qweb;

// The renderer should not handle pagination, data loading, or coordination
// with the control panel. It is only concerned with rendering.
return Widget.extend({
    // Renderer constructor
    // parent: parent widget
    // arch: the arch field of the view to be rendered (already parsed)
    // fields: the 'fields' parameter returned by field_view_get
    // state: a complete description of the state required to render the view
    //       so, basically the record(s) to be displayed
    // widgets_registry: all field widgets
    init: function(parent, arch, fields, state, widgets_registry) {
        this._super(parent);
        this.arch = arch;
        this.fields = fields;
        this.widgets_registry = widgets_registry;

        // the state field is the only base field that should change during
        // the lifetime of the renderer.  When it does change, the view
        // will be rerendered.
        this.state = state;

        // this.widgets is a list of all instantiated field widgets.
        // those widgets will be destroyed and recreated at each
        // rerendering
        this.widgets = [];
    },
    start: function() {
        this.$el.addClass(this.arch.attrs.class);
        return this.render().then(this._super.bind(this));
    },
    // update the state of the view.  It always retrigger a full rerender.
    update: function(state) {
        var local_state = this.get_local_state();
        this.state = state;
        return this.render().then(this.set_local_state.bind(this, local_state));
    },
    // Render the view
    // Be aware that the current field widgets will always be destroyed
    // before the new rendering.
    render: function() {
        _.invoke(this.widgets, 'destroy');
        this.widgets = [];
        return this._render();
    },
    // Actual rendering. Supposed to be overridden by concrete renderers.
    // The basic responsabilities of _render are:
    // * use the xml arch of the view to render a jQuery representation
    // * instantiate a widget from the widgets_registry for each field in the arch
    // Note that the 'state' field should contains all necessary information
    // for the rendering.  The field widgets should be as synchronous as possible,
    // because otherwise, a visible flicker might happen, since the previous
    // content is removed before the rendering start.
    _render: function() {
        return $.when();
    },
    // todo: add and use getWidget method
    getWidget: function(node) {
        // read field type from node
        // or get widget name from attrs
    },
    add_field_tooltip: function(widget, $node) {
        // optional argument $node, the jQuery element on which the tooltip should be attached
        // if not given, the tooltip is attached on the widget's $el
        $node = $node.length ? $node : widget.$el;
        $node.tooltip({
            delay: { show: 1000, hide: 0 },
            title: function() {
                return qweb.render('NewWidgetLabel.tooltip', {
                    debug: core.debug,
                    widget: widget,
                });
            }
        });
    },
    // this method is used to get local state unknown by renderer parent, but
    // necessary to restore the renderer to a full state after an update.  For
    // example, the currently opened tabs in a form view, or the current scrolling
    // position
    get_local_state: function() {
        // to be implemented by actual renderer
    },
    // this method is used after an update (and may also be used after a new renderer
    // is instantiated).  For example, opening a new record in a form view is
    // done by instantiating a new renderer.  But the curently opened page should
    // be maintained if possible.
    set_local_state: function(local_state) {
        // to be implemented by actual renderer
    },
});

});

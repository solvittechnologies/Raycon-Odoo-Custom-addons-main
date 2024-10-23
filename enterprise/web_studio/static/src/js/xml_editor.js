odoo.define('web_studio.XMLEditor', function (require) {
'use strict';

var ajax = require('web.ajax');
var Dialog = require('web.Dialog');

var ace = require('web_editor.ace');

var XMLEditor = ace.ViewEditor.extend({
    init: function(parent, view_id) {
        this._super.apply(this, arguments);
        this.view_id = view_id;
    },
    willStart: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            var defs = [];
            if (!window.ace && !this.loadJS_def) {
                defs.push(ajax.loadJS('/web/static/lib/ace/ace.odoo-custom.js').then(function () {
                    return $.when(ajax.loadJS('/web/static/lib/ace/mode-python.js'),
                        ajax.loadJS('/web/static/lib/ace/mode-xml.js'),
                        ajax.loadJS('/web/static/lib/ace/theme-monokai.js'));
                }));
            }
            defs.push(ajax.jsonRpc('/web_editor/customize_template_get', 'call', {key: self.view_id, full: true}).then(function (views) {
                self.views = views.slice();
                self.template_views = views.slice();
            }));
            return $.when.apply($, defs);
        });
    },
    start: function() {
        this._super();
        var $viewList = this.$('#ace-view-list');
        var viewGraph = this.buildViewGraph(this.views);
        _(viewGraph).each(function (view) {
            if (!view.id) { return; }

            this.views[view.id] = view;
            new ace.ViewOption(this, view).appendTo($viewList);
        }.bind(this));
        var currentArch = this.views[this.view_id].arch;
        this._displayArch(currentArch, this.view_id);
    },
    displayError: function () {
        var error = this._super.apply(this, arguments);
        Dialog.alert(this, '', {
            title: error.title,
            $content: $('<div>').html(error.message)
        });
    },
    displaySelectedView: function () {
        var viewID = this.selectedViewId();
        var currentArch = this.views[viewID].arch;
        if (this.buffers[viewID]) {
            this.displayView(viewID);
        } else {
            this._displayArch(currentArch, viewID);
        }
    },
    saveView: function (session) {
        var self = this;
        var xml = new ace.XmlDocument(session.text);
        var isWellFormed = xml.isWellFormed();
        var def = $.Deferred();

        var view = _.findWhere(this.views, {id: session.id});
        var old_arch = view.arch;
        var new_arch = xml.xml;

        if (isWellFormed === true) {
            this.trigger_up('save_xml_editor', {
                view_id: session.id,
                old_arch: old_arch,
                new_arch: new_arch,
                on_success: function () {
                    def.resolve();
                    view.arch = new_arch;
                },
            });
        } else {
            def.reject(null, session, isWellFormed);
        }
        return def.then(function() {
            var $option = self.$('#ace-view-list').find('[value=' + session.id +']');
            var bufferName = $option.text();
            var dirtyMarker = " (unsaved changes)";
            var index = bufferName.indexOf(dirtyMarker);
            if (index >= 0) {
                $option.text(bufferName.substring(0, index));
            }
        });
    },
    close: function () {
        this.trigger_up('close_xml_editor');
        this.$el.removeClass('oe_ace_open').addClass('oe_ace_closed');
    },
    updateHash: function () {},
});

return XMLEditor;

});

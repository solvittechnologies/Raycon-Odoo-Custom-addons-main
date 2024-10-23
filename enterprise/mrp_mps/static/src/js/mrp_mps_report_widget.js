odoo.define('mrp_mps.mrp_mps_report', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var formats = require('web.formats');
var Model = require('web.Model');
var time = require('web.time');
var ControlPanelMixin = require('web.ControlPanelMixin');
var Dialog = require('web.Dialog');
var session = require('web.session');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');
var SearchView = require('web.SearchView');
var data = require('web.data');
var data_manager = require('web.data_manager');
var pyeval = require('web.pyeval');
var formats = require('web.formats');

var QWeb = core.qweb;
var _t = core._t;

var mrp_mps_report = Widget.extend(ControlPanelMixin, {
    // Stores all the parameters of the action.
    events:{
        'change .o_mps_save_input_text': 'mps_forecast_save',
        'change .o_mps_save_input_supply': 'on_change_quantity',
        'click .open_forecast_wizard': 'mps_open_forecast_wizard',
        'click .o_mps_apply': 'mps_apply',
        'click .o_mps_add_product': 'add_product_wizard',
        'click .o_mps_auto_mode': 'mps_change_auto_mode',
        'click .o_mps_generate_procurement': 'mps_generate_procurement',
        'mouseover .o_mps_visible_procurement': 'visible_procurement_button',
        'mouseout .o_mps_visible_procurement': 'invisible_procurement_button',
        'click .o_mps_product_name': 'open_mps_product',
    },
    init: function(parent, action) {
        var self = this;
        this.actionManager = parent;
        this.action = action;
        this.fields_view;
        this.searchview;
        this.domain = [];
        return this._super.apply(this, arguments);
    },
    render_search_view: function(){
        var self = this;
        var defs = [];
        new Model('ir.model.data').call('get_object_reference', ['product', 'product_template_search_view']).then(function(view_id){
            self.dataset = new data.DataSetSearch(this, 'product.product');
            var def = data_manager
            .load_fields_view(self.dataset, view_id[1], 'search', false)
            .then(function (fields_view) {
                self.fields_view = fields_view;
                var options = {
                    $buttons: $("<div>"),
                    action: this.action,
                    disable_groupby: true,
                };
                self.searchview = new SearchView(self, self.dataset, self.fields_view, options);
                self.searchview.on('search_data', self, self.on_search);
                self.searchview.appendTo($("<div>")).then(function () {
                    defs.push(self.update_cp());
                    self.$searchview_buttons = self.searchview.$buttons.contents();
                });
            });
        });
    },
    willStart: function() {
        return this.get_html();
    },
    start: function() {
        var self = this;
        this.period;
        this.render_search_view();
        return this._super.apply(this, arguments).then(function () {
            self.$el.html(self.html);
        });
    },
    on_change_quantity: function(e) {
        var self = this;
        var $input = $(e.target);
        var target_value = formats.parse_value($input.val().replace(String.fromCharCode(8209), '-'), {type: 'float'}, false);
        if(isNaN(target_value) && target_value !== false) {
            this.do_warn(_t("Wrong value entered!"), _t("Only Integer Value should be valid."));
        } else {
            return new Model('sale.forecast').call('save_forecast_data', [
                 parseInt($input.data('product')), target_value, $input.data('date'), $input.data('date_to'), $input.data('name')],
                 {context: session.user_context})
                .then(function() {
                    self.get_html().then(function() {
                        self.re_renderElement();
                    });
            });
        }
    },
    visible_procurement_button: function(e){
        clearTimeout(this.hover_element);
        $(e.target).find('.o_mps_generate_procurement').removeClass('o_form_invisible');
    },
    invisible_procurement_button: function(e){
        clearTimeout(this.hover_element);
        this.hover_element = setTimeout(function() {
            $(e.target).find('.o_mps_generate_procurement').addClass('o_form_invisible');
        }, 100);
    },
    mps_generate_procurement: function(e){
        var self = this;
        var target = $(e.target);
        return new Model('sale.forecast').call('generate_procurement',
                [parseInt(target.data('product')), 1],
                {context: session.user_context})
        .then(function(result){
            if (result){
                self.get_html().then(function() {
                    self.re_renderElement();
                });
            }
        });
    },
    mps_change_auto_mode: function(e){
        var self = this;
        var target = $(e.target);
        return new Model('sale.forecast').call('change_forecast_mode',
            [parseInt(target.data('product')), target.data('date'), target.data('date_to'), parseInt(target.data('value'))],
            {context: session.user_context})
        .then(function(result){
            self.get_html().then(function() {
                self.re_renderElement();
            });
        });
    },
    mps_show_line: function(e){
        var classes = $(e.target).data('value');
        if(!$(e.target).is(':checked')){
            $('.'+classes).hide();
        }
        else{
            $('.'+classes).show();
        }
    },
    re_renderElement: function() {
        this.$el.html(this.html);
    },
    option_mps_period: function(e){
        var self = this;
        this.period = $(e.target).parent().data('value');
        var model = new Model('mrp.mps.report');
        return model.call('search', [[]]).then(function(res){
                return model.call('write',
                    [res, {'period': self.period}],
                    {context: session.user_context})
                .done(function(result){
                self.get_html().then(function() {
                    self.update_cp();
                    self.re_renderElement();
                });
            });
        });
    },
    add_product_wizard: function(e){
        var self = this;
        return new Model('ir.model.data').call('get_object_reference', ['mrp_mps', 'mrp_mps_report_view_form']).then(function(data){
            return self.do_action({
                name: _t('Add a Product'),
                type: 'ir.actions.act_window',
                res_model: 'mrp.mps.report',
                views: [[data[1] || false, 'form']],
                target: 'new',
            })
        });
    },
    open_mps_product: function(e){
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "product.product",
            res_id: parseInt($(e.target).data('product')),
            views: [[false, 'form']],
        });
    },
    mps_open_forecast_wizard: function(e){
        var self = this;
        var product = $(e.target).data('product') || $(e.target).parent().data('product');
        return new Model('ir.model.data').call('get_object_reference', ['mrp_mps', 'product_product_view_form_mps']).then(function(data){
            return self.do_action({
                name: _t('Forecast Product'),
                type: 'ir.actions.act_window',
                res_model: 'product.product',
                views: [[data[1] || false, 'form']],
                target: 'new',
                res_id: product,
            });
        });
    },
    mps_forecast_save: function(e){
        var self = this;
        var $input = $(e.target);
        var target_value = formats.parse_value($input.val().replace(String.fromCharCode(8209), '-'), {type: 'float'}, false);
        if(isNaN(target_value) && target_value !== false) {
            this.do_warn(_t("Wrong value entered!"), _t("Only Integer or Float Value should be valid."));
        } else {
            return new Model('sale.forecast').call('save_forecast_data', [
                    parseInt($input.data('product')), target_value, $input.data('date'), $input.data('date_to'), $input.data('name')],
                    {context: session.user_context})
                .done(function(res){
                    self.get_html().then(function() {
                        self.re_renderElement();
                    });
                })
        }
    },
    on_search: function (domains) {
        var self = this;
        var result = pyeval.sync_eval_domains_and_contexts({
            domains: domains
        });
        this.domain = result.domain;
        this.get_html().then(function() {
            self.re_renderElement();
        });
    },
    mps_apply: function(e){
        var self = this;
        var product = parseInt($(e.target).data('product'));
        return new Model('mrp.mps.report').call('update_indirect',
                [product],
                {context: session.user_context})
        .then(function(result){
            self.get_html().then(function() {
                self.re_renderElement();
            });
        });
    },
    // Fetches the html and is previous report.context if any, else create it
    get_html: function() {
        var self = this;
        var defs = [];
        return new Model('mrp.mps.report').call('get_html',
            [this.domain],
            {context: session.user_context})
        .then(function (result) {
            self.html = result.html;
            self.report_context = result.report_context;
            self.render_buttons();
        });
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        var self = this;
        if (!this.$buttons) {
            this.render_buttons();
        }
        this.$searchview_buttons = $(QWeb.render("MPS.optionButton", {period: self.report_context.period}))
        this.$searchview_buttons.siblings('.o_mps_period_filter');
        this.$searchview_buttons.find('.o_mps_option_mps_period').bind('click', function (event) {
            self.option_mps_period(event);
        });
        this.$searchview_buttons.siblings('.o_mps_columns_filter');
        this.$searchview_buttons.find('.o_mps_option_mps_columns').bind('click', function (event) {
            self.mps_show_line(event);
        });
        this.update_control_panel({
            breadcrumbs: this.actionManager.get_breadcrumbs(),
            cp_content: {
                $buttons: this.$buttons,
                $searchview: this.searchview.$el,
                // $searchview_buttons: this.$searchview_buttons,
                $searchview_buttons: this.$searchview_buttons
            },
            searchview: this.searchview,
        });
    },
    do_show: function() {
        this._super();
        this.update_cp();
    },
    render_buttons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("MPS.buttons", {}));
        this.$buttons.on('click', function(){
            new Model('sale.forecast').call('generate_procurement_all',
                [],
                {context: session.user_context})
            .then(function(result){
                self.get_html().then(function() {
                    self.re_renderElement();
                });
            });
        });
        return this.$buttons;
    },
});

core.action_registry.add("mrp_mps_report", mrp_mps_report);
return mrp_mps_report;
});

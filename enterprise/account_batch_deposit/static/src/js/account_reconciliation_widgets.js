odoo.define('account_batch_deposit.reconciliation_custom', function (require) {
"use strict";

var Model = require('web.Model');
var CrashManager = require('web.CrashManager');
var widgets = require('account.reconciliation');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

widgets.bankStatementReconciliation.include({

    init: function(parent, context) {
        this._super(parent, context);
        this.batch_deposits = [];
    },

    serverPreprocessResultHandler: function(data) {
        this._super(data);
        this.batch_deposits = data.batch_deposits;
    },

    updateBatchDeposits: function() {
        var self = this;
        return new Model("account.bank.statement")
            .call("get_batch_deposits_data", [self.statement_ids || undefined])
            .then(function(data) {
                self.batch_deposits = data;
                _.each(self.getChildren(), function(child) {
                    child.render_batch_deposits_selector();
                });
            });
    },

    processReconciliations: function(reconciliations) {
        if (_.any(reconciliations, function(r) { return r.batch_deposit_id !== false }))
            this.updateBatchDeposits();
        return this._super(reconciliations);
    },

    childValidated: function(child) {
        if (child.batch_deposit_id !== false)
            this.updateBatchDeposits();
        return this._super(child);
    },

});

widgets.bankStatementReconciliationLine.include({

    events: _.defaults({
        "click .batch_deposit": "batchDepositClickHandler",
    }, widgets.bankStatementReconciliationLine.prototype.events),

    init: function(parent, context) {
        this._super(parent, context);
        this.batch_deposit_id = false;
    },

    render: function() {
        this._super();
        this.render_batch_deposits_selector();
    },

    render_batch_deposits_selector: function() {
        var self = this;
        this.$(".match_controls .batch_deposits_selector").remove();
        if (this.st_line && this.st_line.has_no_partner) {
            // Select deposits from the same journal as the bank statement
            var relevant_deposits = _.filter(this.getParent().batch_deposits, function(d) { return d.journal_id === self.st_line.journal_id });
            this.$(".match_controls .filter").after(QWeb.render("batch_deposits_selector", {
                batch_deposits: relevant_deposits,
            }));
        }
    },

    batchDepositClickHandler: function(e) {
        e.preventDefault();
        var self = this;
        var deposit_id = parseInt(e.currentTarget.dataset.batch_deposit_id);
        new Model("account.bank.statement.line")
            .call("get_move_lines_for_reconciliation_widget_by_batch_deposit_id", [this.line_id, deposit_id])
            .then(function (deposit_lines) {
                // Check if some lines are already selected in another reconciliation
                var lines_selected_here_ids = _.map(self.get("mv_lines_selected"), function(l) { return l.id });
                var lines_not_selected_here = _.filter(deposit_lines, function(l) { return lines_selected_here_ids.indexOf(l.id) === -1 });
                var excluded_ids = _.reduce(self.getParent().excluded_move_lines_ids, function(memo, val) { return memo.concat(val) }, []);
                var lines_selected_elsewhere = _.filter(lines_not_selected_here, function(l) { return excluded_ids.indexOf(l.id) !== -1 });
                if (lines_selected_elsewhere.length > 0) {
                    var message = _t("Some journal items from the selected batch deposit are already selected in another reconciliation : ");
                    message += _.map(lines_selected_elsewhere, function(l) { return l.name }).join(', ');
                    new CrashManager().show_warning({data: {
                        exception_type: _t("Incorrect Operation"),
                        message: message,
                    }});
                    return;
                }
                // Select lines and set batch_deposit_id
                _.each(deposit_lines, function(line) { self.decorateMoveLine(line) }, self);
                self.set("lines_created", []);
                var line_ids = _.map(deposit_lines, function(l) { return l.id });
                self.mv_lines_deselected = _.filter(self.mv_lines_deselected, function(l){ return line_ids.indexOf(l.id) === -1 });
                self.set("mv_lines_selected", deposit_lines);
                self.batch_deposit_id = deposit_id;
            });
    },
});

});

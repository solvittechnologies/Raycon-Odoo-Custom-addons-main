odoo.define('stock_barcode.picking_type_kanban', function (require) {
'use strict';

var KanbanRecord = require('web_kanban.Record');

KanbanRecord.include({
    on_card_clicked: function () {
        if (this.model === 'stock.picking.type') {
            this.$('button').first().click();
        } else {
            this._super.apply(this, arguments);
        }
    }
});

});

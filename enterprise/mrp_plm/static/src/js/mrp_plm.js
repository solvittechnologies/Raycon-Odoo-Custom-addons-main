odoo.define('mrp_plm.update_kanban', function (require) {

var core = require('web.core');
var Model = require('web.Model');

var KanbanRecord = require('web_kanban.Record');

var QWeb = core.qweb;


KanbanRecord.include({
    on_kanban_action_clicked: function(ev) {
        var self = this;
        if (this.model === 'mrp.eco' && $(ev.currentTarget).data('type') === 'set_cover') {
            ev.preventDefault();
            new Model('ir.attachment').query(['id', 'name'])
               .filter([['res_model', '=', 'mrp.eco'], ['res_id', '=', this.id], ['mimetype', 'ilike', 'image']])
               .all().then(function (attachment_ids) {

                    var $cover_modal = $(QWeb.render("mrp_plm.SetCoverModal", {
                        widget: self,
                        attachment_ids: attachment_ids,
                    }));

                    $cover_modal.appendTo($('body'));
                    $cover_modal.modal('toggle');
                    $cover_modal.on('click', 'img', function(ev){
                        self.update_record({
                            data : {
                                displayed_image_id: $(ev.currentTarget).data('id'),
                            }
                        });
                        $cover_modal.modal('toggle');
                        $cover_modal.remove();
                    });
            });
        } else {
            this._super.apply(this, arguments, ev);
        }
    },
});
});

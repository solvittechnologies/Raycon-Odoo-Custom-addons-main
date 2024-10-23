odoo.define('project_timesheet_synchro.Session', function (require) {
"use strict";

var Session = require('web.Session');


// Includes the Session
Session.include({
    session_reload: function () {
        var self = this;
        return this.rpc("/web/session/get_session_info", {}).then(function (result) {
            delete result.session_id;
            _.extend(self, result);
        });
    },
});

});

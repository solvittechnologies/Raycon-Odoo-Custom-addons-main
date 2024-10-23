odoo.define('mail_push.fcm', function (require) {
"use strict";

var mobile = require('web_mobile.rpc');
var session = require('web.session');
var Model = require('web.Model');

//Send info only if client is mobile
if(mobile.methods.getFCMKey){
    var session_info = odoo.session_info;
    if(session_info.fcm_project_id){
        mobile.methods.getFCMKey({'project_id': session_info.fcm_project_id, 'inbox_action': session_info.inbox_action}).then(function(response){
            if(response.success && session_info.device_subscription_ids.indexOf(response.data.subscription_id) == -1){
                new Model("mail_push.device")
                    .call("add_device", [response.data.subscription_id, response.data.device_name, 'fcm'])
            }
        });
    }

}

if(mobile.methods.hashChange){
    var current_hash;
    $(window).bind('hashchange', function(event){
        var hash = event.getState();
        if (!_.isEqual(current_hash, hash)) {
            mobile.methods.hashChange(hash);
        }
        current_hash = hash;
    });
}

});

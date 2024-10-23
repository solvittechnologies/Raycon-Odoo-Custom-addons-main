odoo.define("fastra_licence.database_expire", function(require) {
"use strict";

var AppsMenu = require("web.AppsMenu");
var Dialog = require('web.Dialog');

    AppsMenu.include({
        start: function() {
            this._super.apply(this, arguments);

            if (odoo.session_info.database_block_is_warning) {
                Dialog.alert(this, odoo.session_info.database_expiration_message);
            }

            if (odoo.session_info.database_block_message) {
                $(".database_block_message").html(
                    odoo.session_info.database_block_message
                );

                if (!odoo.session_info.database_block_is_warning) {
                    $(".o_main").block({
                        message: $(".block_ui.database_block_message").html(
                            odoo.session_info.database_block_message
                        ),
                    });
                    $("header").css("z-index", $.blockUI.defaults.baseZ + 20);
                }
            }
        },
    });
});
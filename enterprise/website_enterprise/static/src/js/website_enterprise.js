odoo.define('website.app_switcher', function(require) {
    'use strict';

    var session = require('web.session');
    var website = require('website.website');

    website.TopBar.include({
        start: function() {
            this.$el.one('click', '.o_menu_toggle', function (e) {
                e.preventDefault();

                // We add a spinner for the user to understand the loading.
                $(e.currentTarget).removeClass('fa fa-th').append($('<span/>', {'class': 'fa fa-spin fa-spinner'}));
                var url = "/web#home";
                window.location.href = session.debug ? $.param.querystring(url, {debug: session.debug}) : url;
            });

            return this._super.apply(this, arguments);
        },
    });
});

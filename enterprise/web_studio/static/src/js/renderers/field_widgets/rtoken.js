odoo.define('web_studio.rtoken', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var pyeval = require('web.pyeval');
var framework = require('web.framework');
var field_registry = require('web.field_registry');

var _t = core._t;


var rtoken = AbstractField.extend({
    template: 'website_version.GoogleAccess',
    start: function() {
      var self = this;
      this.$el.on('click', 'button.GoogleAccess', function() {
          if (self.mode !== 'readonly') {
              self.allow_google();
          }
      });
      return this._super.apply(this, arguments);
  },
  allow_google: function() {
    var self = this;
    $('button.GoogleAccess').prop('disabled', true);
    var context = pyeval.eval('context');
    self.rpc('/website_version/google_access', {
        fromurl: window.location.href,
        local_context: context
    }).done(function(o) {
        if (o.status === "need_auth") {
            alert(_t("You will be redirected to Google to authorize access to your Analytics Account!"));
            framework.redirect(o.url);
        }
        else if (o.status === "need_config_from_admin"){
          if (confirm(_t("The Google Management API key needs to be configured before you can use it, do you want to do it now?"))) {
              self.do_action(o.action);
          }
        }
    }).always(function() { $('button.GoogleAccess').prop('disabled', false); });
  },
});

field_registry.add('rtoken', rtoken);

});

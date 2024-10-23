odoo.define('website_contract.website_contract', function (require) {
    'use strict';
    
    var website = require('website.website');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var payment_form = require('website_payment.payment_form');
    if(!$('.oe_website_contract').length) {
        return $.Deferred().reject("DOM doesn't contain '.oe_website_contract'");
    }
    payment_form.include({
        start: function () {
            this._super()
            this.$target.on("change", 'select[name="pay_meth"]', this.showSubscriptionAcquirer.bind(this));
            this.$('select[name="pay_meth"]').change();
        },
        
        showSubscriptionAcquirer: function(ev) {
            var $new_payment_method = $('#new_payment_method');
            var $form = $(ev.target).parents('form');
            var has_val = parseInt($(ev.target).val()) !== -1;
            $new_payment_method.toggleClass('hidden', has_val);
            $form.find('button').toggleClass('hidden', !has_val);
            this.updateNewPaymentDisplayStatus();
        },
        onSubmit: function(ev) {
            // if we are submitting a new pm form and not the main form, then need to intervene
            var pm_id = parseInt(this.$('select[name="pay_meth"]').val());
            var $main_form = $('#wc-payment-form');
            if (pm_id === -1) {
                ev.preventDefault();
                ev.stopPropagation();
                var $form = $(ev.target);
                var action = $form.attr('action');
                var data = this.getFormData($form);
                this.createToken(ev, data, action).then(function (data) {
                    if (data) {
                        $main_form.find('select[name="pay_meth"]').append('<option value="'+data+'"/>')
                        $main_form.find('select[name="pay_meth"]').val(data);
                        $main_form[0].submit();
                    }
                }).fail(function(message, data){
                    $(self).attr('disabled', false);
                    $(self).find('i').remove();
                    $(core.qweb.render('website.error_dialog', {
                        title: core._t('Error'),
                        message: core._t("<p>We are not able to add your payment method at the moment.<br/> Please try again later or contact us.</p>") + (core.debug ? data.data.message : '')
                    })).appendTo("body").modal('show');
                });
            } else {
                return $main_form[0].submit();
            }
        }
    });
    return;
});
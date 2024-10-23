odoo.define('voip.core', function(require) {
"use strict";

var bus = require('bus.bus').bus;
var core = require('web.core');
var Model = require('web.Model');
var web_client = require('web.web_client');
var Class = core.Class;
var mixins = core.mixins;
var _t = core._t;

var UserAgent = Class.extend(core.mixins.PropertiesMixin,{
    init: function(parent,options){
        core.mixins.PropertiesMixin.init.call(this,parent);
        this.onCall = false;
        this.incoming_call = false;
        new Model("voip.configurator").call("get_pbx_config").then(_.bind(this.init_ua,this));
        this.blocked = false;
    },

    //initialisation of the ua object
    init_ua: function(result){
        this.mode = result.mode;
        if(this.mode == "prod"){
            var ua_config = {};
            if(!(result.login && result.pbx_ip && result.password)){
                this.trigger_error(_t('One or more parameter is missing. Please check your configuration.'));
                return;
            }
            ua_config = {
                uri: result.login +'@'+result.pbx_ip,
                wsServers: result.wsServer || null,
                authorizationUser: result.login,
                password: result.password,
                hackIpInContact: true,
                log: {builtinEnabled: false},
            };
            this.always_transfer = result.always_transfer;
            this.external_phone = result.external_phone;
            this.ring_number = result.ring_number;
            try{
                var self = this;
                this.ua = new SIP.UA(ua_config);
                //catch the error if the ws uri is wrong
                this.ua.transport.ws.onerror = function(e){
                    self.trigger_error(_t('The websocket uri could be wrong. Please check your configuration.'));
                };
            }catch(err){
                this.trigger_error(_t('The server configuration could be wrong. Please check your configuration.'));
                return;
            }
            this.ua.on('invite', function (invite_session){
                var name = invite_session.remoteIdentity.displayName;
                var number = invite_session.remoteIdentity.uri.user;
                var content = _t("From ") + name + ' (' + number + ')';
                var title = _t('Incoming call');
                self.ringbacktone.currentTime = 0;
                self.ringbacktone.play();
                self.notification = self.send_notification(title, content);
                function reject_invite(ev) {
                    if(!self.incoming_call){
                        self.ringbacktone.pause();
                        invite_session.reject();
                    }
                }
                invite_session.on('rejected', function(){
                    if (self.notification) {
                        self.notification.removeEventListener('close',reject_invite);
                        self.notification.close('rejected');
                        self.notification = undefined;
                        self.ringbacktone.pause();
                    } else {
                        alert(_t("Call hanged up by the customer before answering."));
                    }
                });
                if (self.notification){
                    self.notification.onclick = function(){
                        window.focus();
                        self.ringbacktone.pause();
                        var call_options = {
                            media: {
                                render: {
                                    remote: self.remote_audio
                                }
                            }
                        };
                        invite_session.accept(call_options);
                        self.onCall = true;
                        self.incoming_call = true;
                        self.sip_session = invite_session;
                        self.trigger('sip_incoming_call');
                        //Bind action when the call is hanged up
                        invite_session.on('bye',_.bind(self.bye,self));
                        this.close();
                    };
                    self.notification.addEventListener('close',reject_invite);
                }else{
                    var confirmation = confirm(_t("Incoming call from ") + name + ' (' + number + ')');
                    if(confirmation){
                        self.ringbacktone.pause();
                        if (self.onCall) {
                           self.hangup();
                        }
                        var call_options = {
                            media: {
                                render: {
                                    remote: self.remote_audio
                                }
                            }
                        };
                        invite_session.accept(call_options);
                        self.onCall = true;
                        self.incoming_call = true;
                        self.sip_session = invite_session;
                        self.trigger('sip_incoming_call');
                        //Bind action when the call is hanged up
                        invite_session.on('bye',_.bind(self.bye,self));
                    }else{
                        invite_session.reject();
                        self.ringbacktone.pause();
                    }
                }
            });
        }
        this.remote_audio = document.createElement("audio");
        this.remote_audio.autoplay = "autoplay";
        $("html").append(this.remote_audio);
        this.ringbacktone = document.createElement("audio");
        this.ringbacktone.loop = "true";
        this.ringbacktone.src = "/voip/static/src/sounds/ringbacktone.mp3";
        $("html").append(this.ringbacktone);
    },

    // TODO when the send_notification is moved into utils instead of mail.utils
    // remove this function and use the one in utils
    send_notification: function(title, content) {
        if (window.Notification && Notification.permission === "granted") {
            return new Notification(title, {body: content, icon: "/mail/static/src/img/odoo_o.png", silent: true});
        }
    },

    trigger_error: function(msg, temporary){
        this.trigger('sip_error', msg, temporary);
        this.blocked = true;
    },

    _make_call: function() {
        if(this.sip_session){
            return;
        }
        var call_options = {
            media: {
                stream: this.media_stream,
                render: {
                    remote: this.remote_audio
                }
            }
        };    
        try{
            //Make the call
            this.sip_session = this.ua.invite(this.current_number,call_options);
        }catch(err){
            this.trigger_error(_t('the connection cannot be made. ')+
                _t('Please check your configuration.</br> (Reason receives :') + response.reason_phrase+')');
            return;
        }
        //Bind action when the call is answered
        this.sip_session.on('accepted',_.bind(this.accepted,this));
        //Bind action when the call is in progress to catch the ringing phase
        this.sip_session.on('progress', _.bind(this.progress,this));
        //Bind action when the call is rejected by the customer
        this.sip_session.on('rejected',_.bind(this.rejected,this));
        //Bind action when the call is transfered
        this.sip_session.on('refer',function(response){console.log("REFER");console.log(response);});
        //Bind action when the user hangup the call while ringing
        this.sip_session.on('cancel',_.bind(this.cancel,this));
        //Bind action when the call is hanged up
        this.sip_session.on('bye',_.bind(this.bye,this));
    },

    rejected: function(response){
        this.sip_session = false;
        clearTimeout(this.timer);
        this.timer = null;
        this.trigger('sip_rejected');
        this.sip_session = false;
        this.ringbacktone.pause();
        if(response.status_code == 404 || response.status_code == 488){
            this.trigger_error(
                _.str.sprintf(_t('The number is incorrect, the user credentials could be wrong or the connection cannot be made. Please check your configuration.</br> (Reason receives :%s)',
                    response.reason_phrase)),
                true);
        }
    },

    bye: function(){
        clearTimeout(this.timer);
        this.timer = null;
        this.sip_session = false;
        this.onCall = false;
        if(this.incoming_call){
            this.incoming_call = false;
            this.trigger('sip_end_incoming_call');
        }else{
            this.trigger('sip_bye');
        }
        if(this.mode == "demo"){
            clearTimeout(this.timer_bye);
        }
    },

    cancel: function(){
        this.sip_session = false;
        clearTimeout(this.timer);
        this.timer = null;
        this.ringbacktone.pause();
        this.trigger('sip_cancel');
        if(this.mode == "demo"){
            clearTimeout(this.timer_bye);
        }
    },

    progress: function(response){
        var self = this;
        // some version of asterisk don't send ringing but only trying
        if(response.reason_phrase == "Ringing" || response.reason_phrase == "Trying"){
            this.trigger('sip_ringing');
            this.ringbacktone.play();
            //set the timer to stop the call if ringing too long
            if(!this.timer){
                this.timer = setTimeout(function(){
                    self.trigger('sip_customer_unavailable');
                    self.sip_session.cancel();
                },4000*self.ring_number);
            }
        }
    },

    accepted: function(result){
        this.onCall = true;
        clearTimeout(this.timer);
        this.timer = null;
        this.ringbacktone.pause();
        this.trigger('sip_accepted');
        if(this.always_transfer){
            this.sip_session.refer(this.external_phone);
        }
    },

    make_call: function(number){
        if(this.mode == "demo"){
            var response = {'reason_phrase': "Ringing"};
            var self = this;
            this.trigger('sip_ringing');
            this.ringbacktone.play();
            var timer_accepted = setTimeout(function(){
                self.accepted(response);
            },5000);
            this.timer_bye = setTimeout(function(){
                self.bye();
            },10000);
            return;
        }
        this.current_number = number.replace(/[\s-/.\u00AD]/g, '');

        //if there is already a media stream, it is reused
        if (this.media_stream) {
            this._make_call();
        } else {
            if (SIP.WebRTC.isSupported()) {
                /*      
                    WebRTC method to get a media stream      
                    The callbacks functions are getUserMediaSuccess, when the function succeed      
                    and getUserMediaFailure when the function failed
                    The _.bind is used to be ensure that the "this" in the callback function will still be the same
                    and not become the object "window"        
                */ 
                var mediaConstraints = {
                    audio: true,
                    video: false
                };
                SIP.WebRTC.getUserMedia(mediaConstraints, _.bind(media_stream_success,this), _.bind(no_media_stream,this));
            }else{
                this.trigger_error(_t('Your browser could not support WebRTC. Please check your configuration.'));
            }
        }
        function media_stream_success(stream){
            this.media_stream = stream;
            this._make_call();
        }
        function no_media_stream(e){
            this.trigger_error(_t('Problem during the connection. Check if the application is allowed to access your microphone from your browser.'), true);
            console.error('getUserMedia failed:', e);
        }
    },

    hangup: function(){
        if(this.mode == "demo"){
            if(this.onCall){
                this.bye();
            }else{
                this.cancel();
            }
        }
        if(this.sip_session){
            if(this.onCall){
                this.sip_session.bye();
            }else{
                this.sip_session.cancel();
            }
        }
    },

    transfer: function(number){
        if(this.sip_session){
            this.sip_session.refer(number);
        }
    },

    send_dtmf: function(number){
        if(this.sip_session){
            this.sip_session.dtmf(number);
        }
    },
});

return {
    UserAgent: UserAgent
};
});
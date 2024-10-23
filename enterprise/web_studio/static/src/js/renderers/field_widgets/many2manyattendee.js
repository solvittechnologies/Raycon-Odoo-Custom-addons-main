odoo.define('web_studio.many2manyattendee', function (require) {
"use strict";

var field_registry = require('web.field_registry');
var relational_fields = require('web.relational_fields');

var FieldMany2ManyTags = relational_fields.FieldMany2ManyTags;

var Many2ManyAttendee = FieldMany2ManyTags.extend({
    tag_template: "Many2ManyAttendeeTag",
    // FIXME: This widget used to refetch the relational data fields needed to
    //        its rendering. Basically, all usual fields for tags plus "status".
    //        This can't currently be done with the current implementation of
    //        the new view. For now, the attendee tags will be missing the
    //        status indicator in studio mode.
});

field_registry.add('many2manyattendee', Many2ManyAttendee);

});

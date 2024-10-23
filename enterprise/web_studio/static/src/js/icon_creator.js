odoo.define('web_studio.IconCreator', function (require) {
"use strict";

var Widget = require('web.Widget');
var core = require('web.core');

var QWeb = core.qweb;

var IconCreator = Widget.extend({
    template: 'web_studio.IconCreator',
    events: {
        'click .o_web_studio_selector': 'on_selector',
    },

    init: function() {

        this.available_colors = [
            '#FFFFFF',
            '#51CAB2',
            '#4D4D4D',
            '#61BD4F',
            '#F2D600',
            '#FFAB4A',
            '#EB5A46',
            '#875A7B',
            '#0079BF',
            '#00C2E0',
            '#4CD98E',
            '#FF80CE',
            '#B6BBBF',
        ];

        this.available_icons = [
            'fa fa-bell',
            'fa fa-calendar',
            'fa fa-circle',
            'fa fa-cube',
            'fa fa-cubes',
            'fa fa-flag',
            'fa fa-folder-open',
            'fa fa-home',
            'fa fa-rocket',
            'fa fa-sitemap',
        ];

        this.palette_templates = {
            'color': 'web_studio.IconCreator.ColorPalette',
            'background_color': 'web_studio.IconCreator.ColorPalette',
            'icon': 'web_studio.IconCreator.IconPalette',
        };

        this.color = this.available_colors[0];
        this.background_color = this.available_colors[1];
        this.icon_class = this.available_icons[0];

        this._super.apply(this, arguments);
    },

    get_value: function() {
        return [this.icon_class, this.color, this.background_color];
    },

    start: function() {
        this.update();

        return this._super.apply(this, arguments);
    },

    update: function() {
        var $new_icon = $('<i>').addClass(this.icon_class).css('color', this.color);
        this.$('.o_app_icon').empty().html($new_icon).css('background-color', this.background_color);

        var $new_selector_icon = $('<i>').addClass(this.icon_class);
        this.$('.o_web_studio_selector[data-type="icon"]').empty().html($new_selector_icon);
        this.$('.o_web_studio_selector[data-type="background_color"]').css('background-color', this.background_color);
        this.$('.o_web_studio_selector[data-type="color"]').css('background-color', this.color);
    },

    on_selector: function(ev) {
        var self = this;
        var selector_type = $(ev.currentTarget).data('type');

        if (!selector_type) { return; }
        if (this.$palette) { this.$palette.remove(); }

        this.$palette = $(QWeb.render(this.palette_templates[selector_type], {widget: this}));
        $(ev.currentTarget).append(this.$palette);
        this.$palette.on('mouseleave', function() {
            $(this).remove();
        });
        this.$palette.find('.o_web_studio_selector').click(function(ev) {
            if (selector_type === 'background_color') {
                self.background_color = $(ev.currentTarget).data('color');
            } else if (selector_type === 'color') {
                self.color = $(ev.currentTarget).data('color');
            } else {
                self.icon_class = $(ev.currentTarget).children('i').attr('class');
            }
            self.update();
        });
    },
});

return IconCreator;

});

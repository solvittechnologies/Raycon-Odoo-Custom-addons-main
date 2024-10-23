odoo.define("website_helpdesk.menu", function (require) {
    "use strict";

    require("web_editor.base");

    var pathname = $(location).attr("pathname");
    var $link = $(".team_menu li a");
    if (pathname !== "/helpdesk/") {
        $link = $link.filter("[href$='" + pathname + "']");
    }
    $link.first().closest("li").addClass("active");

    // TODO: use pager
    $('.o_my_show_more').on('click', function(ev) {
        ev.preventDefault();
        $(this).parents('table').find(".to_hide").toggleClass('hidden');
        $(this).find('span').toggleClass('hidden');
    });
});

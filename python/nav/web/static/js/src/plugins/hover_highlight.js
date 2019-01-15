define([], function () {

    function HoverHighlight(node) {
        this.node = typeof node === 'string' ? $(node) : node;
        addHighlight(this.node);
    }

    function addHighlight(topNode) {
        var bg_colors = {};
        $('a[class^="task_"]', topNode).hover(function () {
            var shared_id = $(this).attr('class').match(/(task_\d+)/)[1];
            var color_id = $(this).attr('class').match(/bg(\d{1})light/)[1];
            bg_colors[shared_id] = color_id;
            $("." + shared_id).removeClass("bg" + color_id + "light");
            $("." + shared_id).addClass("bg" + color_id + "dark");
        }, function () {
            var shared_id = $(this).attr('class').match(/(task_\d+)/)[1];
            var color_id = bg_colors[shared_id];
            $("." + shared_id).removeClass("bg" + color_id + "dark");
            $("." + shared_id).addClass("bg" + color_id + "light");
        });

    }

    return HoverHighlight;

});

require(['plugins/quickselect', 'plugins/hover_highlight', 'libs/jquery'], function (QuickSelect, HoverHighlight) {
    var calendar = $('.calendar');
    var quickselect = $('.quickselect');

    if (calendar.length) {
        new HoverHighlight(calendar);
    }

    if (quickselect.length) {
        new QuickSelect(quickselect);
    }
});
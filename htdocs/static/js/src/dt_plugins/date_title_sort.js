define(['libs/datatables.min'], function () {
    /* Custom sort on date in title - created for NAV */
    jQuery.extend(jQuery.fn.dataTableExt.oSort, {
        "title-date-pre": function (a) {
            if (/Never/.test(a)) {
                return 2;
            } else if (/title="(.*?)"/.test(a)) {
                var timestamp = a.match(/title="(.*?)"/)[1];
                if ($.trim(timestamp) != '') {
                    var splits = $.trim(timestamp).split(' ');
                    var dates = splits[0].split('-');
                    var times = splits[1].split(':');
                    return (dates[0] + dates[1] + dates[2] + times[0] + times[1]) * 1;
                }
            }
            return 1;
        },

        "title-date-asc": function (a, b) {
            return b - a;
        },

        "title-date-desc": function (a, b) {
            return a - b;
        }
    });
});


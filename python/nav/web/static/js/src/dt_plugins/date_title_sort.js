define(['libs/datatables.min'], function () {
    /* Custom sort on date in title - created for NAV */
    $.fn.DataTable.ext.type.order['title-date-pre'] = function (data) {
        if (/Never/.test(data)) {
            return 2;
        } else if (/title="(.*?)"/.test(data)) {
            var timestamp = data.match(/title="(.*?)"/)[1];
            if (timestamp.trim() !== '') {
                var splits = timestamp.trim().split(' ');
                var dates = splits[0].split('-');
                var times = splits[1].split(':');
                return (dates[0] + dates[1] + dates[2] + times[0] + times[1]) * 1;
            }
        }
        return 1;
    };
});

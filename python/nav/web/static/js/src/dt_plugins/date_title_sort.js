define(['libs/datatables.min'], function () {
    /* Custom sort on date in title - created for NAV */
    $.fn.DataTable.ext.type.order['title-date-pre'] = (data) => {
        if (/Never/.test(data)) {
            return 2;
        } else if (/title="(.*?)"/.test(data)) {
            const timestamp = data.match(/title="(.*?)"/)[1];
            if (timestamp.trim() !== '') {
                const [dateStr, timeStr] = timestamp.trim().split(' ');
                const dates = dateStr.split('-');
                const times = timeStr.split(':');
                return (dates[0] + dates[1] + dates[2] + times[0] + times[1]) * 1;
            }
        }
        return 1;
    };
});

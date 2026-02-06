define(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.order['alt-string-pre'] = (data) => {
        return data.match(/alt="(.*?)"/)[1].toLowerCase();
    };
});

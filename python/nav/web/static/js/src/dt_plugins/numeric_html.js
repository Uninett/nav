/*
    Copied from: http://legacy.datatables.net/plug-ins/sorting
    Author: Allan Jardine
*/
require(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.order['num-html-pre'] = function (data) {
        var x = String(data).replace(/<[\s\S]*?>/g, "");
        return parseFloat(x);
    };
});

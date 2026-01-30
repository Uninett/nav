/*
    Copied from: http://legacy.datatables.net/plug-ins/sorting
    Author: Jonathan Romley
*/
require(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.order['percent-pre'] = function (data) {
        var x = (data === "-") ? 0 : data.replace(/%/, "");
        return parseFloat(x);
    };
});

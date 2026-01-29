/*
    Copied from: http://legacy.datatables.net/plug-ins/sorting
    Author: Allan Jardine
*/
require(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.order['num-html-pre'] = (data) => {
        const x = String(data).replace(/<[^>]*>/g, '');
        return parseFloat(x);
    };
});

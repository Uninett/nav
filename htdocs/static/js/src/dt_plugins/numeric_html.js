/*
    Copied from: http://legacy.datatables.net/plug-ins/sorting
    Author: Allan Jardine
*/
require(['libs/datatables.min'], function () {
    jQuery.extend(jQuery.fn.dataTableExt.oSort, {
        "num-html-pre": function (a) {
            var x = String(a).replace(/<[\s\S]*?>/g, "");
            return parseFloat(x);
        },

        "num-html-asc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },

        "num-html-desc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    });
});

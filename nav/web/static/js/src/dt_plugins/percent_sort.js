/*
    Copied from: http://legacy.datatables.net/plug-ins/sorting
    Author: Jonathan Romley
*/
require(['libs/datatables.min'], function () {
    jQuery.extend(jQuery.fn.dataTableExt.oSort, {
        "percent-pre": function (a) {
            var x = (a == "-") ? 0 : a.replace(/%/, "");
            return parseFloat(x);
        },

        "percent-asc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },

        "percent-desc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    });
});

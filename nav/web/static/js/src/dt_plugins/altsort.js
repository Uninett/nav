define(['libs/datatables.min'], function () {
    jQuery.extend(jQuery.fn.dataTableExt.oSort, {
        "alt-string-pre": function (a) {
            return a.match(/alt="(.*?)"/)[1].toLowerCase();
        },

        "alt-string-asc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        },

        "alt-string-desc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        }
    });
});


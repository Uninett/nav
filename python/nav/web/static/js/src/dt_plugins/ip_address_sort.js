/*
 * Copied from http://www.datatables.net/plug-ins/sorting
 * Author: Brad Wasson
 */
require(['libs/datatables.min'], function() {
    $.fn.DataTable.ext.type.order['ip-address-pre'] = function (data) {
        var m = data.split("."), x = "";

        for (var i = 0; i < m.length; i++) {
            var item = m[i];
            if (item.length === 1) {
                x += "00" + item;
            } else if (item.length === 2) {
                x += "0" + item;
            } else {
                x += item;
            }
        }

        return x;
    };
});

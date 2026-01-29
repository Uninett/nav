/*
 * Copied from http://www.datatables.net/plug-ins/sorting
 * Author: Brad Wasson
 */
require(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.order['ip-address-pre'] = (data) => {
        return data.split('.').map((octet) => octet.padStart(3, '0')).join('');
    };
});

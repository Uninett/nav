/*
 * Copied from http://www.datatables.net/plug-ins/type-detection
 * Author: Brad Wasson
 */

require(['libs/datatables.min'], function () {
    $.fn.DataTable.ext.type.detect.unshift((data) => {
        if (/^\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}$/.test(data)) {
            return 'ip-address';
        }
        return null;
    });
});

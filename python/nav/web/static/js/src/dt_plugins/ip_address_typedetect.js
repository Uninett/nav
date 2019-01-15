/*
 * Copied from http://www.datatables.net/plug-ins/type-detection
 * Author: Brad Wasson
 */

require(['libs/datatables.min'], function() {
    jQuery.fn.dataTableExt.aTypes.unshift(
        function ( sData )
        {
            if (/^\d{1,3}[\.]\d{1,3}[\.]\d{1,3}[\.]\d{1,3}$/.test(sData)) {
                return 'ip-address';
            }
            return null;
        }
    );
});

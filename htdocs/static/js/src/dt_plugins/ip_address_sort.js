/*
 * Copied from http://www.datatables.net/plug-ins/sorting
 * Author: Brad Wasson
 */
require(['libs/datatables.min'], function() {
    jQuery.extend( jQuery.fn.dataTableExt.oSort, {
        "ip-address-pre": function ( a ) {
            var m = a.split("."), x = "";
            
            for(var i = 0; i < m.length; i++) {
                var item = m[i];
                if(item.length == 1) {
                    x += "00" + item;
                } else if(item.length == 2) {
                    x += "0" + item;
                } else {
                    x += item;
                }
            }
            
            return x;
        },
        
        "ip-address-asc": function ( a, b ) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },
        
        "ip-address-desc": function ( a, b ) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    } );
    
});

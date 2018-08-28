/*
 This module is used for sorting based on module-name in NAV. It's highly
 targetted at sorting specifically Cisco modules based on module-number
 */
define(['dt_plugins/natsort', 'libs/datatables.min'], function (naturalSort, DataTables) {
    function moduleSort(a, b) {
        a = strip_tags(a);
        b = strip_tags(b);
        if (bothAreStrings(a, b) && bothAreCiscoInterfaceNames(a, b)) {
            return naturalSort(
                a.slice(a.search(/\d/)),
                b.slice(b.search(/\d/))
            );
        } else {
            return naturalSort(a, b);
        }
    }

    function bothAreCiscoInterfaceNames(a, b) {
        return isCiscoInterfaceName(a) && isCiscoInterfaceName(b);
    }

    function isCiscoInterfaceName(ifname) {
        return ifname.match(/(gi|fa|te)\d+\/\d+/i);
    }

    function bothAreStrings(a, b) {
        return typeof(a) === 'string' && typeof(b) === 'string';
    }

    function strip_tags(input) {
        return $('<div>' + input + '</div>').text();
    }

    $.extend(DataTables.ext.oSort, {
        "module-asc": function (a, b) {
            return moduleSort(a, b);
        },

        "module-desc": function (a, b) {
            return moduleSort(b, a);
        }
    });

    return moduleSort;

});

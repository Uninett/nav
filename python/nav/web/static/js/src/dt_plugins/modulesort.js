/*
 This module is used for sorting based on module-name in NAV. It's highly
 targetted at sorting specifically Cisco modules based on module-number
 */
define(['dt_plugins/natsort', 'libs/datatables.min'], function (naturalSort) {
    function moduleSort(a, b) {
        a = stripTags(a);
        b = stripTags(b);
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
        return typeof a === 'string' && typeof b === 'string';
    }

    function stripTags(input) {
        return $(`<div>${input}</div>`).text();
    }

    $.fn.DataTable.ext.type.order['module-pre'] = (data) => data;

    $.fn.DataTable.ext.type.order['module-asc'] = (a, b) => moduleSort(a, b);

    $.fn.DataTable.ext.type.order['module-desc'] = (first, second) => moduleSort(second, first);

    return moduleSort;

});

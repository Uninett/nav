/*
 This module is used for sorting based on module-name in NAV. It's highly
 targetted at sorting specifically Cisco modules based on module-number
 */
define(['dt_plugins/natsort', 'libs/jquery.dataTables.min'], function (naturalSort) {
    function moduleSort(a, b) {
        if (bothAreStrings(a, b) && bothAreCiscoInterfaceNames(a, b)) {
            return naturalSort.naturalSort(
                a.slice(a.search(/\d/)),
                b.slice(b.search(/\d/)));
        } else {
            return naturalSort.naturalSort(a, b)
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

    if (jQuery.fn.dataTableExt) {
        jQuery.extend(jQuery.fn.dataTableExt.oSort, {
            "module-asc": function (a, b) {
                return moduleSort(a, b);
            },

            "module-desc": function (a, b) {
                return moduleSort(a, b) * -1;
            }
        });
    }

    return {
        moduleSort: moduleSort
    }

});


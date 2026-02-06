define(['libs/datatables.min'], function () {
    /*
     * Natural Sort algorithm for Javascript - Version 0.7 - Released under MIT license
     * Author: Jim Palmer (based on chunking idea from Dave Koelle)
     * Contributors: Mike Grier (mgrier.com), Clint Priest, Kyle Adams, guillermo
     * See: http://js-naturalsort.googlecode.com/svn/trunk/naturalSort.js
     */
    function naturalSort(a, b) {
        const re = /(^-?[0-9]+(\.?[0-9]*)[df]?e?[0-9]?$|^0x[0-9a-f]+$|[0-9]+)/gi;
        const sre = /(^[ ]*|[ ]*$)/g;
        const ore = /^0/;
        // convert all to strings and trim()
        const x = a.toString().replace(sre, '') || '';
        const y = b.toString().replace(sre, '') || '';
        // chunk/tokenize
        const xN = x.replace(re, '\0$1\0').replace(/\0$/, '').replace(/^\0/, '').split('\0');
        const yN = y.replace(re, '\0$1\0').replace(/\0$/, '').replace(/^\0/, '').split('\0');
        // natural sorting through split numeric strings and default strings
        const numS = Math.max(xN.length, yN.length);
        for (let cLoc = 0; cLoc < numS; cLoc++) {
            // find floats not starting with '0', string or 0 if not defined (Clint Priest)
            let oFxNcL = !(xN[cLoc] || '').match(ore) && parseFloat(xN[cLoc]) || xN[cLoc] || 0;
            let oFyNcL = !(yN[cLoc] || '').match(ore) && parseFloat(yN[cLoc]) || yN[cLoc] || 0;
            // handle numeric vs string comparison - number < string - (Kyle Adams)
            if (isNaN(oFxNcL) !== isNaN(oFyNcL)) return isNaN(oFxNcL) ? 1 : -1;
            // rely on string comparison if different types - i.e. '02' < 2 != '02' < '2'
            else if (typeof oFxNcL !== typeof oFyNcL) {
                oFxNcL += '';
                oFyNcL += '';
            }
            if (oFxNcL < oFyNcL) return -1;
            if (oFxNcL > oFyNcL) return 1;
        }
        return 0;
    }

    $.fn.DataTable.ext.type.order['natural-pre'] = (data) => data;

    $.fn.DataTable.ext.type.order['natural-asc'] = (a, b) => naturalSort(a, b);

    $.fn.DataTable.ext.type.order['natural-desc'] = (a, b) => naturalSort(a, b) * -1;

    return naturalSort;
});

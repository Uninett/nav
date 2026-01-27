/**
 * Custom tablesort extensions for NAV
 * Provides IP address sorting and datetime sorting
 */
define(['tablesort'], function(Tablesort) {

    /**
     * Extract IPv4 address from a string that may contain other text
     */
    function extractIP(str) {
        const match = str.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);
        return match ? match[1] : str;
    }

    /**
     * IP Address sorting extension
     * Pads each octet to 3 digits for correct string comparison
     * e.g., "192.168.1.1" becomes "192168001001"
     */
    Tablesort.extend('ip-address', function(item) {
        // Match strings containing IPv4 addresses
        return /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(item);
    }, function(a, b) {
        function padOctets(ip) {
            const extracted = extractIP(ip);
            return extracted.split('.').map(function(octet) {
                return ('00' + octet).slice(-3);
            }).join('');
        }
        const aPadded = padOctets(a);
        const bPadded = padOctets(b);
        return bPadded.localeCompare(aPadded);
    });

    /**
     * ISO datetime sorting extension
     * Handles special values "first" and "last" for sorting
     */
    Tablesort.extend('iso-datetime', function(item) {
        // Match ISO datetime or special values
        return /^\d{4}-\d{2}-\d{2}/.test(item) || item === 'first' || item === 'last';
    }, function(a, b) {
        function getValue(val) {
            if (val === 'last') return Number.NEGATIVE_INFINITY;
            if (val === 'first') return Number.POSITIVE_INFINITY;
            return new Date(val).getTime();
        }
        return getValue(b) - getValue(a);
    });

    /**
     * Helper function to initialize tablesort with jquery-tablesorter-like config
     *
     * @param {HTMLElement} table - The table element to sort
     * @param {Object} options - Configuration options
     * @param {Object} options.headers - Column configuration (0-indexed)
     *   - { sorter: false } disables sorting
     *   - { sorter: 'ip-address' } sets sort method
     * @param {Object} options.textExtraction - Custom text extraction functions
     * @param {boolean} options.descending - Sort descending by default
     * @param {Array} options.sortList - Initial sort [[columnIndex, direction]]
     *   where direction is 0 for ascending, 1 for descending
     */
    function initTableSort(table, options) {
        options = options || {};
        const headers = table.querySelectorAll('thead th');

        // Apply header configurations
        if (options.headers) {
            Object.keys(options.headers).forEach(function(index) {
                const config = options.headers[index];
                const header = headers[parseInt(index, 10)];
                if (!header) return;

                if (config.sorter === false) {
                    header.setAttribute('data-sort-method', 'none');
                } else if (config.sorter) {
                    header.setAttribute('data-sort-method', config.sorter);
                }
            });
        }

        // Apply text extraction by setting data-sort-value attributes on cells
        if (options.textExtraction) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(function(row) {
                const cells = row.querySelectorAll('td');
                Object.keys(options.textExtraction).forEach(function(index) {
                    const extractFn = options.textExtraction[index];
                    const cell = cells[parseInt(index, 10)];
                    if (cell && typeof extractFn === 'function') {
                        const sortValue = extractFn(cell);
                        cell.setAttribute('data-sort-value', sortValue);
                    }
                });
            });
        }

        // Handle initial sort via sortList option
        // Format: [[columnIndex, direction]] where direction 0=asc, 1=desc
        if (options.sortList && options.sortList.length > 0) {
            const sortCol = options.sortList[0][0];
            const sortDir = options.sortList[0][1];
            const sortHeader = headers[sortCol];
            if (sortHeader) {
                sortHeader.setAttribute('data-sort-default', '');
                if (sortDir === 1) {
                    sortHeader.setAttribute('data-sort-reverse', '');
                }
            }
        }

        // Initialize tablesort with sortAttribute for data-sort-value compatibility
        const sortOptions = {
            sortAttribute: 'sort-value'
        };
        if (options.descending) {
            sortOptions.descending = true;
        }

        return new Tablesort(table, sortOptions);
    }

    return {
        Tablesort: Tablesort,
        init: initTableSort
    };
});

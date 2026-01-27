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
     * Pad IP octets to 3 digits for correct string comparison
     * e.g., "192.168.1.1" becomes "192168001001"
     */
    function padOctets(ip) {
        const extracted = extractIP(ip);
        return extracted.split('.').map(function(octet) {
            return ('00' + octet).slice(-3);
        }).join('');
    }

    /**
     * Get sortable value for datetime, handling special values
     */
    function getDatetimeValue(val) {
        const trimmed = val.trim();
        if (trimmed === 'last') return Number.NEGATIVE_INFINITY;
        if (trimmed === 'first' || trimmed === 'Still active') return Number.POSITIVE_INFINITY;
        return new Date(trimmed).getTime();
    }

    /**
     * Numeric sorting extension
     * Extracts numbers from strings like ">6", "<10", ">=28", "5.5", etc.
     */
    Tablesort.extend('number', function(item) {
        // Match strings containing numbers (with optional operators/units)
        return /[−-]?\d+\.?\d*/.test(item);
    }, function(a, b) {
        // Extract first number from each string (handle minus sign variants)
        const aMatch = a.replace('−', '-').match(/-?\d+\.?\d*/);
        const bMatch = b.replace('−', '-').match(/-?\d+\.?\d*/);
        const aNum = aMatch ? Number.parseFloat(aMatch[0]) : 0;
        const bNum = bMatch ? Number.parseFloat(bMatch[0]) : 0;
        return bNum - aNum;
    });

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
     * Handles special values "first", "last", and "Still active" for sorting
     */
    Tablesort.extend('iso-datetime', function(item) {
        // Match ISO datetime or special values
        const trimmed = item.trim();
        return /^\d{4}-\d{2}-\d{2}/.test(trimmed) || trimmed === 'first' || trimmed === 'last' || trimmed === 'Still active';
    }, function(a, b) {
        const aVal = getDatetimeValue(a);
        const bVal = getDatetimeValue(b);
        // Handle equal values to avoid NaN from infinity - infinity
        if (aVal === bVal) return 0;
        return bVal - aVal;
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

        // Check if a column has all identical values (sorting would be meaningless)
        function hasIdenticalValues(colIndex) {
            const cells = table.querySelectorAll(`tbody tr td:nth-child(${colIndex + 1})`);
            const values = new Set([...cells].map(cell => {
                // Use data-sort attribute if present, otherwise textContent
                return cell.dataset.sort ?? cell.textContent.trim();
            }));
            return values.size <= 1;
        }

        // Apply header configurations
        // Set 'alpha' as default for all columns to prevent auto-detection issues
        // (empty columns cause [].every() to return true, selecting wrong sorter)
        headers.forEach(function(header, index) {
            // Disable sorting for columns with all identical values
            if (hasIdenticalValues(index)) {
                header.dataset.sortMethod = 'none';
                return;
            }

            const config = options.headers?.[index];
            if (config) {
                if (config.sorter === false) {
                    header.setAttribute('data-sort-method', 'none');
                } else if (config.sorter) {
                    header.setAttribute('data-sort-method', config.sorter);
                }
            } else if (!header.dataset.sortMethod) {
                header.dataset.sortMethod = 'alpha';
            }
        });

        // Apply text extraction by setting data-sort attributes on cells
        if (options.textExtraction) {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(function(row) {
                const cells = row.querySelectorAll('td');
                Object.keys(options.textExtraction).forEach(function(index) {
                    const extractFn = options.textExtraction[index];
                    const cell = cells[parseInt(index, 10)];
                    if (cell && typeof extractFn === 'function') {
                        const sortValue = extractFn(cell);
                        cell.dataset.sort = sortValue;
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

        // Initialize tablesort
        const sortOptions = {};
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

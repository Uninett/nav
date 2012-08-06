define(['libs/jquery.dataTables.min'], function () {
    /*
     * Primary filter is the main filter run on all tables
     * Secondary filters are run together with the primary filter
     */

    var tables = [];
    var primary_node = '';

    var filters = {
        last_seen: {
            runner: filter_last_seen,
            node: '#last_seen'
        }
    };

    function add_filters(node, input_tables, secondary_filters) {
        if (!node) {
            throw Error('Need node to attach primary filter to');
        }
        add_primary_filter(node, input_tables);
        add_secondary_filters(secondary_filters);
    }

    function add_primary_filter(node, input_tables) {
        primary_node = node;
        tables = input_tables;
        $(primary_node).keyup(do_primary_filter);
    }

    function do_primary_filter() {
        var filter = $(primary_node).val();
        for (var i = 0; i < tables.length; i++) {
            $(tables[i]).dataTable().fnFilter(filter);
        }
    }


    /*
     * Add all secondary filters
     * filters_to_enable: list of config-objects
     * config-object:
     *    - name: name of existing filter
     *    - node (optional): node to attach keylistener
     */
    function add_secondary_filters(filters_to_enable) {
        for (var i = 0; i < filters_to_enable.length; i++) {
            var filter_config = filters_to_enable[i];

            if (!filter_config.name) {
                throw Error('filter config did not have name');
            }

            if (!filters[filter_config.name]) {
                throw Error('filter ' + filter_config.name + ' does not exist.')
            }

            var config = filters[filter_config.name];

            if (filter_config.node) {
                config.node = filter_config.node;
            }

            register_filter(config)
        }
    }

    /* Attach keylistener and register filter to datatable plugin */
    function register_filter(config) {
        $(config.node).keyup(do_primary_filter);
        $.fn.dataTableExt.afnFiltering.push(config.runner);
    }

    /*
     * Secondary filters
     */

    /* Filter on row 4 and 5 */
    function filter_last_seen(oSettings, aData, iDataIndex) {
        var days = parseInt($(filters.last_seen.node).val());

        if (days) {
            var rowdate = extract_date(aData[4]);
            return (!is_trunk(aData[3]) && daysince(rowdate) >= days);
        } else {
            return true;
        }
    }

    /*
     * Helper functions
     */

    /* Extract date without time from string */
    function extract_date(cell) {
        var match = cell.match(/\d{4}-\d{2}-\d{2}/);
        if (match) {
            return new Date(match[0]);
        } else {
            return new Date('1970-01-01');
        }
    }


    /* Find days since input date */
    function daysince(date) {
        var one_day = 1000 * 60 * 60 * 24;
        var now = new Date();
        var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        var reset_date = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        return Math.round((today - reset_date) / one_day);
    }


    /* Find if cell is trunk or not */
    function is_trunk(cell) {
        return /trunk/i.test(cell);
    }


    return {
        add_filters: add_filters,
        filter_last_seen: filter_last_seen,
        extract_date: extract_date,
        daysince: daysince,
        is_trunk: is_trunk
    };

});


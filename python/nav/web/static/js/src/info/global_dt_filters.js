define(['libs/datatables.min'], function () {
    /*
     * Primary filter is the main filter run on all tables
     * Secondary filters are run together with the primary filter
     */

    var tables = [];
    var primary_node = '';

    function add_filters(node, input_tables, secondary_filters) {
        if (!node) {
            throw new Error('Need node to attach primary filter to');
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
        var filter = remove_keywords($(primary_node).val());
        for (var i = 0; i < tables.length; i++) {
            $(tables[i]).dataTable().fnFilter(filter);
        }
    }

    function remove_keywords(input) {
        var words = input.split(' ');
        var notkeywords = [];
        for (var i=0; i<words.length; i++) {
            if (words[i].slice(0, 1) !== '$') {
                notkeywords.push(words[i]);
            }
        }
        return notkeywords.join(' ');
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
            var filter = filters_to_enable[i];

            if (!filters[filter]) {
                throw new Error('filter ' + filter + ' does not exist.');
            }

            register_filter(filters[filter]);
        }
    }

    /* Attach keylistener and register filter to datatable plugin */
    function register_filter(config) {
        $.fn.dataTableExt.afnFiltering.push(config.runner);
        $('#' + config.node + ' input').keyup(do_primary_filter);
    }

    /*
     * Secondary filters
     */

    /* Filter on column 5 (last active) when column 4 (vlan) is not trunk.
     * Very reusable code! ;-P */
    function filter_last_seen(oSettings, aData, iDataIndex) {
        var days = get_keyword(/\$days:\w+/) || getInputValue(filters.last_seen.node);
        if (days) {
            var rowdate = extract_date(aData[4]);
            return (!is_trunk(aData[3]) && daysince(rowdate) >= days);
        }
        return true;
    }


    /* Filter on vlan */
    function filter_vlan(oSettings, aData, iDataIndex) {
        var vlan = get_keyword(/\$vlan:\w+/) || getInputValue(filters.vlan.node);
        if (vlan) {
            return vlan === aData[3];
        }
        return true;
    }

    /*
     * Helper functions
     */
    function get_keyword(regexp) {
        var input = $(primary_node).val();
        var keyword = input.match(regexp);
        if (keyword) {
            return keyword[0].split(':')[1];
        }
        return '';
    }


    function getInputValue(node) {
        return $('#' + node).find('input').val();
    }

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

    var filters = {
        last_seen: {
            name: 'Last Seen',
            node: 'lastseenfilter',
            runner: filter_last_seen
        },
        vlan: {
            name: 'Vlan',
            node: 'vlanfilter',
            runner: filter_vlan
        }
    };

    return {
        add_filters: add_filters,
        filter_last_seen: filter_last_seen,
        filter_vlan: filter_vlan,
        extract_date: extract_date,
        daysince: daysince,
        is_trunk: is_trunk,
        remove_keywords: remove_keywords
    };

});


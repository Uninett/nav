require([
    'src/info/tab_navigation',
    'src/info/global_dt_filters',
    'src/info/table_info_converter',
    'jquery-1.4.4.min',
    'jquery-ui-1.8.21.custom.min',
    'jquery.dataTables.min',
    'downloadify.min'
], function (tab_navigation, global_dt_filters, table_info_converter) {
    /* Run javascript at document ready */
    $(document).ready(function () {
        if ($('#infotabs')) {
            add_tabs();
            add_navigation();
        }
    });

    /* Add tabs to roomview content */
    function add_tabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            ajaxOptions: {
                beforeSend: request_before_send,
                error: request_error,
                success: request_success,
                complete: request_complete
            }
        };
        var tabs = $('#infotabs').tabs(tabconfig);
        $('#infotabs').show();
    }

    function request_before_send(req) {
        req.setRequestHeader('X-NAV-AJAX', 'true');
    }

    function request_error(xhr, status, error) {
        if (xhr.status == 401) {
            window.location = '/index/login/?origin=' + window.location.href;
        } else {
            $('<div class="messages error">Could not load netbox interfaces</div>').appendTo('#ui-tabs-1');
        }
    }

    function request_success() {
        enrich_tables();
        add_filters();
        add_csv_download();
    }

    function request_complete() {
        $('.tab-spinner').hide();
    }

    /* Add navigation to jQuery ui tabs */
    function add_navigation() {
        var wrapper = $('#infotabs');
        tab_navigation.add(wrapper);
    }

    /* Enrich tables with dataTables module */
    function enrich_tables() {
        var dt_config = {
            bAutoWidth: false,
            bFilter: true,
            bInfo: true,
            bLengthChange: false,
            bPaginate: false,
            bSort: true,
            aoColumns: [
                {'sType': 'natural'},
                {'sType': 'string'},
                {'sType': 'alt-string'},
                {'sType': 'natural'},
                {'sType': 'title-date'}
            ],
            fnInfoCallback: format_filter_text
        };

        $('table.netbox').dataTable(dt_config);

    }

    /* Custom format of search filter text */
    function format_filter_text(oSettings, iStart, iEnd, iMax, iTotal, sPre) {
        if (iEnd == iMax) {
            return "Showing " + iMax + " entries.";
        } else {
            var entrytext = iEnd == 1 ? "entry" : "entries";
            return "Showing " + iEnd + " " + entrytext + " (filtered from " + iMax + " entries).";
        }
    }

    /* Add global filtering to the tables */
    function add_filters() {
        var tables = $.fn.dataTable.fnTables();
        var primary_node = $('#netbox-global-search');
        var filters = [
            {
                name: 'last_seen',
                node: $('#last-seen')
            }
        ];

        try {
            global_dt_filters.add_filters(primary_node, tables, filters);
        } catch (error) {
            console.log(error.message);
        }
    }

    function add_csv_download() {
        var tables = $('#netboxes table.netbox');

        var config = {
            filename: 'interfaces.csv',
            data: function () {
                return table_info_converter.create_csv(tables);
            },
            transparent: false,
            swf: '/js/extras/downloadify.swf',
            downloadImage: '/images/roominfo/csv.png',
            width: 41,
            height: 13,
            append: false
        };
        $('#downloadify').downloadify(config);
    }
});
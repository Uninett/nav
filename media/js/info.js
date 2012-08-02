var NAV = this.NAV || {};

(function(){

    /* Run javascript at document ready */
    $(document).ready(function(){
        if ($('#infotabs')) {
            add_tabs();
            add_navigation();
        }
    });

    /* Add tabs to roomview content */
    function add_tabs() {
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
        add_last_seen_filter();
        add_csv_download();
    }

    function request_complete() {
        $('.tab-spinner').hide();
    }

    /* Add navigation (bookmark and history) to tabs */
    function add_navigation() {
        /* Mark selected tab on page load */
        select_tab_on_load();

        /* Set hash mark with index when a tab is selected */
        $('#infotabs').bind('tabsselect', function(event, ui) {
            if (ui.index != 0 || window.location.hash) {
                window.location.hash = ui.index;
            }
        });

        /* On hash change, navigate to the tab indicated in hash mark */
        $(window).bind('hashchange', function(event) {
            navigate();
        });

        /* Mark selected tab on page load */
        function select_tab_on_load() {
            navigate();
        }

        /* Navigate to correct tab based on url hash mark */
        function navigate() {
            var $tabs = $('#infotabs').tabs();
            var index = 0;
            if (window.location.hash) {
                index = parseInt(window.location.hash.substring(1));
            }

            if (index != $tabs.tabs('option', 'selected')) {
                $tabs.tabs('select', index);
            }
        }

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

        // Add global search filter
        if (tables.length > 1) {
            $('#global-search').show();
            $('#netbox-global-search').keyup(do_global_filter);
        }

        // Add filter on last seen
        $('#last-seen').keyup(do_global_filter);

        function do_global_filter(event) {
            var filter = $('#netbox-global-search').val();
            for (var i=0; i<tables.length; i++) {
                $(tables[i]).dataTable().fnFilter(filter);
            }
        }

    }

    /* Add specific filter on last seen */
     function add_last_seen_filter() {
         $.fn.dataTableExt.afnFiltering.push(filter_last_seen);
     }

    /* Filter used by DataTable to filter based on last seen */
    function filter_last_seen(oSettings, aData, iDataIndex) {
        var days = parseInt($('#last-seen').val());

        if (days) {
            var rowdate = extract_date(aData[4]);
            return (!is_trunk(aData[3]) && daysince(rowdate) >= days);
        } else {
            return true;
        }
    }

    /*
     * Extract these to some kind of util class?
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

    function add_csv_download() {
        var config = {
            filename: 'interfaces.csv',
            data: create_csv,
            transparent: false,
            swf: '/js/downloadify.swf',
            downloadImage: '/images/roominfo/csv.png',
            width: 41,
            height: 13,
            append: false
        };
        $('#downloadify').downloadify(config);
    }

    /* Todo: TEST */
    function create_csv() {
        var content = [];

        $('#netboxes table.netbox').each(function(index, table){
            $(table).find('tbody tr').each(function(index, row){
                var rowdata = format_rowdata(row);
                content.push(rowdata.join(','));
            });
        });

        return content.join('\n');
    }

    /* Todo: TEST */
    function format_rowdata(row) {
        var rowdata = [];
        $(row).find('td').each(function(index, cell){
            if (index == 2) {
                rowdata.push($(cell).find('img').attr('alt'));
            } else {
                rowdata.push(cell.innerText);
            }
        });
        return rowdata;
    }

    /* Make these functions available for testing */
    NAV.info = {
        is_trunk: is_trunk,
        daysince: daysince,
        extract_date: extract_date,
        filter_last_seen: filter_last_seen
    };

})();

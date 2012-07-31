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
        }
    }

    function request_success() {
        enrich_tables();
        add_filters();
        add_last_seen_filter();
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

         function filter_last_seen(oSettings, aData, iDataIndex) {
             var days = parseInt($('#last-seen').val());

             if (days) {
                 var rowdate = extract_date(aData[4]);
                 return (!is_trunk(aData[3]) && daysince(rowdate) >= days);
             } else {
                 return true;
             }
         }

         function extract_date(cell) {
             return new Date(cell.match(/\d{4}-\d{2}-\d{2}/));
         }

         function daysince(date) {
             var one_day = 1000 * 60 * 60 * 24;
             var now = new Date();
             var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
             return Math.round((today - date) / one_day);
         }

         function is_trunk(cell) {
             return /trunk/i.test(cell);
         }

     }


})();

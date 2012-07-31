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
        add_global_filter();
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
    function add_global_filter() {
        var tables = $.fn.dataTable.fnTables();
        if (tables.length > 1) {
            $('#global-search').show();
            $('#netbox-global-search').keyup(apply_global_filter);
        }

        function apply_global_filter(event) {
            var filter = event.currentTarget.value;
            for (var i=0; i<tables.length; i++) {
                $(tables[i]).dataTable().fnFilter(filter);
            }
        }

    }

    /* Add specific filter on last seen */
     function add_filter_last_seen() {
         $.fn.dataTableExt.afnFiltering.push(filter_last_seen);

         function filter_last_seen(oSettings, aData, iDataIndex) {
             var days = parseInt($('#last-seen').value) || 2;

             // Get date from row
             var date = extract_date(aData[4]);

             // Find days since date

             // Compare with days given

             return true;
         }

         function extract_date(cell) {
             return new Date('2012-07-29 20:00');
         }

     }


})();

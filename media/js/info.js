/* Create js namespace for info page */
var infopage = {};

/* Add tabs to roomview content */
infopage.add_roomview_tabs = function() {
    var tabconfig = {
        cache: true, // cache loaded pages
        spinner: '<img src="/images/main/process-working.gif">',
        ajaxOptions: {
            beforeSend: function(req) {
                req.setRequestHeader('X-NAV-AJAX', 'true');
            },
            error: function(xhr, status, error) {
                if (xhr.status == 401) {
                    window.location = '/index/login/?origin=' + window.location.href;
                }
            },
            complete: function() {
                $('.tab-spinner').hide();
                infopage.add_table_sorter();
                infopage.add_global_filter();
            }
        }
    };
    var tabs = $('#infotabs').tabs(tabconfig);
};

/* Add navigation (bookmark and history) to tabs */
infopage.add_navigation = function() {
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

};

/* Add sorting on table row clicks */
infopage.add_table_sorter = function() {
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

    function format_filter_text(oSettings, iStart, iEnd, iMax, iTotal, sPre) {
        if (iEnd == iMax) {
            return "Showing " + iMax + " entries.";
        } else {
            var entrytext = iEnd == 1 ? "entry" : "entries";
            return "Showing " + iEnd + " " + entrytext + " (filtered from " + iMax + " entries).";
        }
    }

};

/* Add global filtering to the tables */
infopage.add_global_filter = function() {
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

};

/* Run javascript at document ready */
$(document).ready(function(){
    if ($('#infotabs')) {
        infopage.add_roomview_tabs();
        infopage.add_navigation();
    }
});

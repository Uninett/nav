
/* Create js namespace for info page */
var infopage = {};

/* Add tabs to roomview content */
infopage.add_roomview_tabs = function() {
    var tabconfig = {
        cache: true, // cache loaded pages
        ajaxOptions: {
            beforeSend: function(req) {
                req.setRequestHeader('X-NAV-AJAX', 'true');
            },
            error: function(xhr, status, error) {
                if (xhr.status == 401) {
                    window.location = '/index/login/?origin=' + window.location.href;
                }
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


/* Run javascript at document ready */
$(document).ready(function(){
    if ($('#infotabs')) {
        infopage.add_roomview_tabs();
        infopage.add_navigation();
    }
});



require([
    "plugins/table_utils", "plugins/tab_navigation", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation) {

    var mainTabsSelector = '#loggerinfotabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        //new TableUtil($('#hostinfo')).addRowToggleTrigger();

        NAV.addGlobalAjaxHandlers();
        if ($(mainTabsSelector).length != 0) {
            addMainTabs();
        }
    });

    function addMainTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            load: eventLoadingComplete
        };
        var tabs = $(mainTabsSelector).tabs(tabconfig);
        tabs.show();
        TabNavigation.add(mainTabsSelector);
    }

    function eventLoadingComplete(event, ui) {
        if (ui.tab.text.trim() === 'Direct Search' || ui.tab.text.trim() === 'Group Search') {
            attachButtonListeners()
        }
    }

    function attachButtonListeners() {
        $('#syslog_search_form button').on('click', function (event) {
            event.preventDefault();
            searchSyslog($(this).data('target'));
        });
    }

    function searchSyslog(target) {
        $.get(target, $("#syslog_search_form").serialize(), function (data) {
            // todo: need error checking.
            $('#syslog_search').html(data);
            attachButtonListeners()
        });
    }
});

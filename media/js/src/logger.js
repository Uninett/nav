require([
    "plugins/table_utils", "plugins/tab_navigation", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation) {

    var mainTabsSelector = '#loggerinfotabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        new TableUtil($('#hostinfo')).addRowToggleTrigger();

        NAV.addGlobalAjaxHandlers();
        if ($(mainTabsSelector).length != 0) {
            addModuleTabs();
            addMainTabs();
        }
    });

    function addModuleTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            load: addActivityButtonListener
        };
        $(moduleTabsSelector).tabs(tabconfig);
    }

    function addMainTabs() {
        var tabs = $(mainTabsSelector).tabs();
        tabs.show();
        TabNavigation.add(mainTabsSelector);
    }

});

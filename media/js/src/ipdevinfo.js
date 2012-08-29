require.config({
    baseUrl: "/js/",
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery-1.4.4.min']
    }
});
require([
    "src/ipdevinfo/table_utils", "src/info/tab_navigation", "libs/jquery-1.4.4.min", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation) {

    var mainTabsSelector = '#ipdevinfotabs';
    var moduleTabsSelector = '#moduletabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        new TableUtil($('table.datasources')).addRowToggleTrigger();
        new TableUtil($('#hostinfo')).addRowToggleTrigger();

        addGlobalAjaxHandlers();
        addModuleTabs();
        addMainTabs();
    });

    function addModuleTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            load: addActivityButtonListener
        };
        $(moduleTabsSelector).tabs(tabconfig);
        TabNavigation.add(mainTabsSelector);
    }

    function addMainTabs() {
        var tabs = $(mainTabsSelector).tabs();
        tabs.show();
    }

    /*
     * Specific for module tabs
     * Add listener to button to recheck switch port activity
     */
    function addActivityButtonListener(event, element) {
        if (element.index != 1) {
            return;
        }
        var activityTab = findActivityTab();
        var button = activityTab.find('form button');

        button.click(function (event) {
            event.preventDefault();
            addIntervalToRequest();
            $(moduleTabsSelector).tabs('load', 1);
        });
    }

    function findActivityTab() {
        var widget = $(moduleTabsSelector).tabs('widget');
        return $('#ui-tabs-2', widget);
    }

    function addIntervalToRequest() {
        $(moduleTabsSelector).tabs("option", "ajaxOptions", {
            data: {
                'interval': getActivityInterval()
            }
        });
    }

    function getActivityInterval() {
        var activityTab = findActivityTab();
        return $('form input[type=text]', activityTab).val();
    }

});

require(["plugins/table_utils", "plugins/tab_navigation", "plugins/neighbor-map", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation, NeighborMap) {

    var mainTabsSelector = '#ipdevinfotabs';
    var metricTabsSelector = "#metrictabs"
    var moduleTabsSelector = '#moduletabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        new TableUtil($('#hostinfo')).addRowToggleTrigger();

        NAV.addGlobalAjaxHandlers();

        if ($(mainTabsSelector).length !== 0) {
            addModuleTabs();
            addMetricTabs()
            addMainTabs();
        }

        var $neighbornode = $('.neighbormap');
        if ($neighbornode.length) {
            new NeighborMap($neighbornode.get(0));
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
        var tabs = $(mainTabsSelector).tabs({
            cache: true,
            spinner: '<img src="/images/main/process-working.gif">'
        });
        markErrorTabs(tabs);
        tabs.show();
        TabNavigation.add(mainTabsSelector);
    }

    function addMetricTabs() {
        var tabs = $(metricTabsSelector).tabs({
            cache: true,
            spinner: '<img src="/images/main/process-working.gif">'
        });
        tabs.show();
        TabNavigation.add(metricTabsSelector);
    }

    /*
     * Set error-class on tabs marked as error by template
     */
    function markErrorTabs(tabs) {
        $('li[data-mark-as-error="True"]', tabs).removeClass('ui-state-default').addClass('ui-state-error');
    }

    /*
     * Specific for module tabs
     * Add listener to button to recheck switch port activity
     */
    function addActivityButtonListener(event, element) {
        if (element.index !== 1) {
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

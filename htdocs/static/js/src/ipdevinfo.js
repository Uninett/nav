require(["plugins/table_utils", "plugins/tab_navigation", "plugins/neighbor-map", "plugins/jquery_ui_helpers", "plugins/graphfetcher_controller", "libs/jquery", "libs/jquery-ui.min"
], function (TableUtil, TabNavigation, NeighborMap, JUIHelpers) {

    var mainTabsSelector = '#ipdevinfotabs';
    var metricTabsSelector = "#metrictabs";
    var moduleTabsSelector = '#moduletabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        new TableUtil($('#hostinfo')).addRowToggleTrigger();


        if ($(mainTabsSelector).length !== 0) {
            addModuleTabs();
            addMetricTabs();
            addMainTabs();

            /* Add tab navigating here to avoid race conditions */
            TabNavigation.add(mainTabsSelector);
            TabNavigation.add(moduleTabsSelector, mainTabsSelector);
            TabNavigation.add(metricTabsSelector, mainTabsSelector);
        }

        var $neighbornode = $('.neighbormap');
        if ($neighbornode.length) {
            new NeighborMap($neighbornode.get(0));
        }
    });

    function addModuleTabs() {
        var tabconfig = {
            beforeLoad: JUIHelpers.cacheRequest,
            load: addActivityButtonListener
        };
        $(moduleTabsSelector).tabs(tabconfig);

        /* Toggle port legend */
        $('#ports').on('click', '.portlegendToggler', function () {
            $(this).next().toggle();
        });
    }

    function addMainTabs() {
        var tabs = $(mainTabsSelector).tabs({
            beforeLoad: JUIHelpers.cacheRequest
        });
        markErrorTabs(tabs);
        tabs.show();
        addFloatingGlobalControls();
    }

    function addMetricTabs() {
        var tabs = $(metricTabsSelector).tabs({
            beforeLoad: JUIHelpers.cacheRequest
        });
        tabs.show();
    }

    function addFloatingGlobalControls() {
        /* Floats the global controls for all graphs on the Port Metrics tab */
        var toBeFixed = $('.toBeFixed'),
            wrapper = toBeFixed.parent('.toBeFixed-wrapper'),
            toBeFixedClone;
        $(window).scroll(function () {
            var currentY = $(window).scrollTop(),
                startPosY = wrapper.offset().top;
            /* This clone is needed to prevent the page from jumping when 'position: fixed' is set */
            toBeFixedClone = toBeFixedClone ? toBeFixedClone : toBeFixed.clone().hide().appendTo(wrapper);

            if (currentY >= startPosY && !toBeFixed.hasClass('floatme')) {
                toBeFixed.addClass('floatme');
                toBeFixedClone.show();
            } else if (currentY < startPosY && toBeFixed.hasClass('floatme')) {
                toBeFixedClone.hide();
                toBeFixed.removeClass('floatme');
            }
        });
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
        var button = activityTab.find('form input[type=submit]');

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

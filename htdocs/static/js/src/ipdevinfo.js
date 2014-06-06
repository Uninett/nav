require(["plugins/table_utils", "plugins/tab_navigation", "plugins/neighbor-map", "plugins/graphfetcher_controller", "libs/jquery", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil, TabNavigation, NeighborMap) {

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
        }

        var $neighbornode = $('.neighbormap');
        if ($neighbornode.length) {
            new NeighborMap($neighbornode.get(0));
        }
    });

    function addModuleTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="' + NAV.imagePath + '/main/process-working.gif">',
            load: addActivityButtonListener
        };
        $(moduleTabsSelector).tabs(tabconfig);
        TabNavigation.add(moduleTabsSelector, mainTabsSelector);

        /* Toggle port legend */
        $('#ports').on('click', '.portlegendToggler', function () {
            $(this).next().toggle();
        });
    }

    function addMainTabs() {
        var tabs = $(mainTabsSelector).tabs({
            cache: true,
            spinner: '<img src="' + NAV.imagePath + '/main/process-working.gif">'
        });
        markErrorTabs(tabs);
        tabs.show();
        TabNavigation.add(mainTabsSelector);
        addFloatingGlobalControls();
    }

    function addMetricTabs() {
        var tabs = $(metricTabsSelector).tabs({
            cache: true,
            spinner: '<img src="/images/main/process-working.gif">'
        });
        tabs.show();
        TabNavigation.add(metricTabsSelector, mainTabsSelector);
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

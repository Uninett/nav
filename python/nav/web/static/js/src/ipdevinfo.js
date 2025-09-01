require([
    "plugins/table_utils",
    "plugins/tab_navigation",
    "plugins/jquery_ui_helpers",
    "plugins/graphfetcher_controller",
    "libs/jquery",
    "libs/jquery-ui.min",
    "libs/jquery.sparkline",
    "plugins/rickshaw_graph"
], function (TableUtil, TabNavigation, JUIHelpers) {

    var mainTabsSelector = '#ipdevinfotabs';
    var metricTabsSelector = "#metrictabs";
    var moduleTabsSelector = '#moduletabs';
    var activityRecheckSelector = '#switchport_activity_recheck';

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

        addSparkLinesToJobs();
        loadSensorValues();
    });

    const ipdevpollJobsContainer = document.querySelector("#ipdevpoll-jobs");
    if (ipdevpollJobsContainer) {
        ipdevpollJobsContainer.addEventListener("htmx:afterSwap", function() {
            addSparkLinesToJobs();
        });
    }

    function loadSensorValues() {
        var metricMap = {};
        $('.sensor-value').each(function(i, element) {
            metricMap[$(element).data('metric')] = element;
        });
        if (_.isEmpty(metricMap)) { return; }
        getSensorData(metricMap, function(data, metricMap) {
            $.each(data, function(i, metricData) {
                var target = metricData.target;
                var datapoints = metricData.datapoints;
                for (var i = datapoints.length - 1; i >= 0; i--) {
                    var value = datapoints[i][0];
                    if (value !== null) {
                        $(metricMap[target]).html(value);
                        break;
                    }
                }
            });
        });
    }

    function commonPrefix(array){
        var arr = array.concat().sort(),
            a1 = arr[0], a2 = arr[arr.length-1], len = a1.length, i = 0;
        while (i<len && a1.charAt(i) === a2.charAt(i)) i++;
        return a1.substring(0, i);
    }

    function getSensorData(metricMap, updateFunc) {
        var url = NAV.graphiteRenderUrl;
        // under the assumption that all sensors on a single device have a
        // common parent node in the metric tree:
        var target = commonPrefix(_.keys(metricMap)) + '*';
        var data = $.param({
            target: target,
            format: 'json',
            from: '-5min',
            until: 'now'
        }, true);
        var request = $.post(url, data);

        request.done(function (data) {
            updateFunc(data, metricMap);
        });

        request.fail(function () {
            console.log("Error on data request");
        });

    }

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

            if (currentY > startPosY && !toBeFixed.hasClass('floatme')) {
                toBeFixed.addClass('floatme');
                toBeFixedClone.show();
            } else if (currentY <= startPosY && toBeFixed.hasClass('floatme')) {
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
        if (element.tab.attr('id') === 'swportactivetab') {
            $(activityRecheckSelector).find('input[type=submit]').on('click', function (event) {
                event.preventDefault();
                addIntervalToRequest();
                $(moduleTabsSelector).tabs('load', element.tab.index());
            });
        }
    }

    function addIntervalToRequest() {
        $(moduleTabsSelector).tabs({
            beforeLoad: function(event, ui) {
                ui.ajaxSettings.url += '?interval=' + getActivityInterval();
            }
        });
    }

    function getActivityInterval() {
        return $(activityRecheckSelector).find('input[id=id_interval]').val();
    }

    function addSparkLinesToJobs() {
        var formatter = function(sparkline, options, fields) {
            /* The x value is seconds since epoch in local timezone. As
               toLocaleString converts based on UTC values, we cheat and say
             that the timeZone is UTC while keeping the formatting local */
            var date = new Date(fields.x * 1000).toLocaleString({}, {timeZone: 'UTC'});
            return '<div class="jqsfield"><span style="color: ' + fields.color + '">&#9679</span> ' + fields.y + '<br/> ' + date + '</div>';
        };

        var options = {
            type: 'line',
            tooltipFormatter: formatter
        };

        $('#ipdevpoll-jobs .sparkline').each(function() {
            var $element = $(this);
            $element.sparkline($element.data('values'), options);
        });

    }

});

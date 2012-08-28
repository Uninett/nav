require.config({
    baseUrl: "/js/",
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery-1.4.4.min']
    }
});
require([
    "src/ipdevinfo/table_utils", "libs/jquery-1.4.4.min", "libs/jquery-ui-1.8.21.custom.min"
], function (TableUtil) {

    var mainTabsSelector = '#ipdevinfotabs';
    var moduleTabsSelector = '#moduletabs';

    $(document).ready(function () {
        // Plug row toggler on datasources
        new TableUtil($('table.datasources')).addRowToggleTrigger();

        // Plug tabs on page
        addModuleTabs();
        addMainTabs();
    });

    function addModuleTabs() {
        var tabconfig = {
            cache: true, // cache loaded pages
            spinner: '<img src="/images/main/process-working.gif">',
            ajaxOptions: {
                beforeSend: request_before_send,
                error: request_error,
                success: request_success,
                complete: request_complete
            },
            load: addActivityButtonListener
        };
        $(moduleTabsSelector).tabs(tabconfig);
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
        console.log('Adding listener to button');
        var activityTab = findActivityTab();
        var button = activityTab.find('form button');

        button.click(function (event) {
            console.log('button clicked');
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

    /* Request handlers */

    function request_before_send(req) {
        req.setRequestHeader('X-NAV-AJAX', 'true');
    }

    function request_error(xhr, status, error) {
        console.error('Request error');
        if (xhr.status == 401) {
            window.location = '/index/login/?origin=' + window.location.href;
        }
    }

    function request_success() {
    }

    function request_complete() {
    }

});
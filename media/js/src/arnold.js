require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {
        NAV.addGlobalAjaxHandlers();
        addTabs();
    });

    function addTabs() {
        var tabs = $('#arnoldtabs').tabs();
        tabs.show();
    }
});

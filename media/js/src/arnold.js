require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {
        addTabs();
    });

    function addTabs() {
        var tabs = $('#arnoldtabs').tabs();
        tabs.show();
    }
});

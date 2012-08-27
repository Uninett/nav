require.config({
    baseUrl: "/js/",
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery-1.4.4.min']
    }
});
require([
    "src/ipdevinfo/table_utils",
    "libs/jquery-1.4.4.min",
    "libs/jquery-ui-1.8.21.custom.min"
],
function(TableUtil) {
    $(function(){
        // Plug row toggler on datasources
        new TableUtil($('table.datasources')).addRowToggleTrigger();
    });
});
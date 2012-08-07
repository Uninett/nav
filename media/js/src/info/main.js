require.config({
    baseUrl: "/js/",
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery-1.4.4.min'],
        'libs/jquery.dataTables.min': ['libs/jquery-1.4.4.min'],
        'libs/downloadify.min': ['libs/swfobject']
    }
});
require(
    [
        "libs/jquery-1.4.4.min",
        "libs/jquery-ui-1.8.21.custom.min",
        "libs/jquery.dataTables.min",
        "libs/swfobject",
        "libs/downloadify.min",
        "src/dt_plugins/natsort",
        "src/dt_plugins/altsort",
        "src/dt_plugins/date_title_sort",
        "src/dt_plugins/modulesort",
        "src/info/tab_navigation",
        "src/info/global_dt_filters",
        "src/info/table_info_converter",
        "src/info/info"
    ], function() {

    }
);

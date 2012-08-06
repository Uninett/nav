require.config({
    baseUrl: "/js",
    shim: {
        'jquery-ui-1.8.21.custom.min': ['jquery-1.4.4.min'],
        'jquery.dataTables.min': ['jquery-1.4.4.min'],
        'downloadify.min': ['swfobject']
    }
});
require(
    [
        "jquery-1.4.4.min",
        "jquery-ui-1.8.21.custom.min",
        "jquery.dataTables.min",
        "swfobject",
        "downloadify.min",
        "src/dt_plugins/natsort",
        "src/dt_plugins/altsort",
        "src/dt_plugins/date_title_sort",
        "src/info/tab_navigation",
        "src/info/global_dt_filters",
        "src/info/table_info_converter",
        "src/info/info"
    ]
);
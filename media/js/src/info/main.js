require.config({
    baseUrl: "/js",
    paths: {
        dt_plugins: 'src/dt_plugins',
        info: 'src/info'
    },
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
        "dt_plugins/natsort",
        "dt_plugins/altsort",
        "dt_plugins/date_title_sort",
        "info/tab_navigation",
        "info/global_dt_filters",
        "info/table_info_converter",
        "info/info"
    ]
);
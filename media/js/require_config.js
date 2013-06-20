var require = {
    baseUrl: '/js',
    waitSeconds: 7, // default
    paths: {
        "libs": "libs",
        "libs-amd": "resources/libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "info": "src/info",
        "netmap": "src/netmap"
    },
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery'],
        'libs/jquery.dataTables.min': ['libs/jquery'],
        'libs/jquery.tablesorter.min': ['libs/jquery'],
        'libs/jquery.nivo.slider.pack': ['libs/jquery'],
        'libs/downloadify.min': ['libs/jquery', 'libs/swfobject'],
        'libs/spin.min': ['libs/jquery'],
        'libs/underscore': {
            exports: '_'
        },
        'libs/d3.v2': { exports: 'd3' },
        'libs/backbone': {
            deps: ["libs/underscore", "libs/jquery"],
            exports: 'Backbone'
        },
        'libs/backbone-eventbroker': ['libs/backbone']

    }
};

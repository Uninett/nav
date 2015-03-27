var require = {
    baseUrl: '/static/js/prod',
    waitSeconds: 7, // default
    paths: {
        "libs": "libs",
        "moment": "libs/moment.min",
        "resources": "resources",
        "libs-amd": "resources/libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "info": "src/info",
        "netmap": "src/netmap",
        "status": "src/status2"
    },
    shim: {
        'libs/foundation.min': ['libs/jquery', 'libs/modernizr', 'libs/fastclick'],
        'libs/jquery-ui-timepicker-addon': ['libs/jquery-ui-1.8.21.custom.min'],
        'libs/underscore': {
            exports: '_'
        },
        'libs/d3.min': { exports: 'd3' },
        'libs/backbone': {
            deps: ["libs/underscore"],
            exports: 'Backbone'
        },
        'libs/backbone-eventbroker': ['libs/backbone'],
        'libs/rickshaw.min': {
            exports: 'Rickshaw',
            deps: ['libs/d3.v2']
        },
        'src/dt_plugins/ip_address_sort': ['libs/jquery.dataTables.min'],
        'src/dt_plugins/ip_address_typedetect': ['libs/jquery.dataTables.min']
    }
};

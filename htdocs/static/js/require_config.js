var require = {
    baseUrl: '/static/js',
    waitSeconds: 90, // default 7
    paths: {
        "libs": "libs",
        "moment": "libs/moment.min",
        "resources": "resources",
        "libs-amd": "resources/libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "info": "src/info",
        "netmap": "src/netmap",
        "status": "src/status2",
        "d3": "libs/d3.min",
        "d3_tip": "//cdnjs.cloudflare.com/ajax/libs/d3-tip/0.6.7/d3-tip.min",
        "nav-url-utils": "src/plugins/nav-url-utils",
        "rickshaw-utils": "src/plugins/rickshaw-utils"
    },
    shim: {
        'libs/foundation.min': ['libs/modernizr', 'libs/fastclick'],
        'libs/jquery-ui-timepicker-addon': ['libs/jquery-ui.min'],
        'libs/underscore': {
            exports: '_'
        },
        'libs/backbone': {
            deps: ["libs/underscore"],
            exports: 'Backbone'
        },
        'libs/backbone-eventbroker': ['libs/backbone']
    },
    deps: ['libs/jquery']
};

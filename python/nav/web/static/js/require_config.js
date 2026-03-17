var require = {
    baseUrl: '/static/js',
    waitSeconds: 90, // default 7
    paths: {
        "libs": "libs",
        "moment": "libs/moment-2.18.1.min",
        "resources": "resources",
        "libs-amd": "resources/libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "dt_config": "src/dt_config",
        "info": "src/info",
        "netmap": "src/netmap",
        "status": "src/status2",
        "d3": "libs/d3-3.5.5.min",  // rickshaw needs the d3 target defined
        "d3v7": "libs/d3-7.8.3.min",
        "d3tip": "libs/d3tip.min",
        "ol-debug": "libs/ol-debug-4.6.5",
        "openlayers": "libs/openlayers-2.12.min",
        "datatables": "libs/datatables-2.2.2.min",
        "handlebars": "libs/handlebars-5.0.0-alpha.1.min",
        "spin": "libs/spin-2.3.2.min",
        "nav-url-utils": "src/plugins/nav-url-utils",
        "rickshaw-utils": "src/plugins/rickshaw-utils",
        "backbone": "libs/backbone-1.0.0.min",
        "underscore": "libs/underscore-1.7.0",
        "marionette": "libs/backbone.marionette-4.1.3.min",
        "backbone.radio": "libs/backbone.radio-2.0.0.min",
        "vue": "libs/vue-2.2.0.min",
        "driver": "libs/driver-1.3.6.min",
        "tinysort": "libs/tinysort-2.3.6.min",
        "flatpickr": "libs/flatpickr-4.6.13.min",
        "jquery": "libs/jquery-4.0.0.min",
        "jquery-ui": "libs/jquery-ui-1.14.0.min",
        "tablesort": "libs/tablesort-5.7.0.min",
        "jquery-multi-select": "libs/jquery.multiselect-2.4.24.min",
        "select2": "libs/select2-4.1.0-rc.0.min",
    },
    shim: {
        'underscore': {
            exports: '_'
        },
        'backbone': {
            deps: ["underscore"],
            exports: 'Backbone'
        },
        'backbone.radio': {
            deps: ["backbone"],
            exports: "Backbone.Radio"
        },
        'marionette': {
            deps: ["backbone", "backbone.radio"],
            exports: "Marionette"
        },
        'libs/backbone-eventbroker': ['backbone'],
        'datatables': {
            deps: ['jquery']
        },
        'select2': {
            deps: ['jquery']
        },
        'tablesort': {
            exports: 'Tablesort'
        },
    },
    deps: ['jquery']
};

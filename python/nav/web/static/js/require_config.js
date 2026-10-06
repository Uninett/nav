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
        "ol-debug": "libs/ol-debug-4.6.5",
        "openlayers": "libs/openlayers-2.12.min",
        "datatables": "libs/datatables-2.2.2.min",
        "handlebars": "libs/handlebars-5.0.0-alpha.1.min",
        "spin": "libs/spin-2.3.2.min",
        "nav-url-utils": "src/plugins/nav-url-utils",
        "rickshaw-utils": "src/plugins/rickshaw-utils",
        "backbone": "libs/backbone-1.0.0.min",
        "underscore": "libs/underscore-1.7.0.min",
        "marionette": "libs/backbone.marionette-4.1.3.min",
        "backbone.radio": "libs/backbone.radio-2.0.0.min",
        "chartjs": "libs/chart-4.5.1.min",
        "chartjs-adapter-moment": "libs/chartjs-adapter-moment-1.0.1.min",
        "chartjs-plugin-zoom": "libs/chartjs-plugin-zoom-2.2.0.min",
        "driver": "libs/driver-1.3.6.min",
        "flatpickr": "libs/flatpickr-4.6.13.min",
        "jquery": "libs/jquery-4.0.0.min",
        "jquery-ui": "libs/jquery-ui-1.14.0.min",
        "tablesort": "libs/tablesort-5.7.0.min",
        "jquery-multi-select": "libs/jquery.multiselect-2.4.24.min",
        "select2": "libs/select2-4.1.0-rc.0.min",
        "uplot": "libs/uplot-1.6.32.min",
    },
    map: {
        // The Chart.js plugins require these module names. RequireJS treats
        // a name that ends in ".js" as a file URL, so map them to our names.
        '*': {
            'chart.js': 'chartjs',
            'chart.js/helpers': 'plugins/chartjs-helpers',
            'hammerjs': 'plugins/hammerjs-stub'
        }
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
        'uplot': {
            exports: 'uPlot'
        },
    },
    deps: ['jquery']
};

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
        "d3": "libs/d3.min",  // rickshaw needs the d3 target defined
        "d3v4": "libs/d3.v4.min",
        "d3tip": "libs/d3tip.min",
        "nav-url-utils": "src/plugins/nav-url-utils",
         "rickshaw-utils": "src/plugins/rickshaw-utils",
        // need to alias names to marionette can pick them up properly. TODO:
        // consider patching Marionette
        "backbone": "libs/backbone",
        "underscore": "libs/underscore",
        "marionette": "libs/backbone.marionette.min",
        "vue": "libs/vue.min",
        "driver": "libs/driver-1.3.6.min",
        "tinysort": "libs/tinysort-3.1.4.min",
        "flatpickr": "libs/flatpickr-4.6.13.min",
    },
    shim: {
        'libs/underscore': {
            exports: '_'
        },
        'backbone': {
          deps: ["libs/underscore"],
          exports: 'Backbone'
        },
        'marionette': {
          deps: ["backbone"],
          exports: "Marionette"
        },
        'libs/backbone': {
            deps: ["libs/underscore"],
            exports: 'Backbone'
        },
        'libs/backbone-eventbroker': ['libs/backbone']
    },
    deps: ['libs/jquery']
};

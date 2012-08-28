
// Require.js configure shortcut aliases
require.config({
    shim: {
        underscore: {
            exports: '_'
        },
        backbone: {
            deps: ["underscore", "jquery"],
            exports: "Backbone"
        },
        spinjs: {
            exports: "Spinner"
        }
    },
    paths: {
        //loader: 'libs/backbone/loader',
        //jQuery: 'libs/jquery/jquery',
        jquery: 'libs/jquery/jquery', // used by jqueryui-amd ..
        //jQuery: 'libs/jquery/jquery', // used by jqueryui-amd ..
        jqueryui: 'libs/jqueryui',
        underscore: 'libs/underscore/underscore',
        //Underscore: 'libs/underscore/underscore',
        handlebars: 'libs/handlebars/handlebars',
        backbone: 'libs/backbone/backbone',
        backbone_eventbroker: 'libs/backbone/backbone-eventbroker',
        //Backbone: 'libs/backbone/backbone',
        /*text: 'libs/require/text',
         order: 'libs/require/order',*/
        netmapextras: '../netmap-extras',
        spinjs: '../spin.min',
        templates: 'templates'
    },
    urlArgs: "nav=" + (new Date()).getTime()
});

require([

    // Load our app module and pass it to our definition function
    'app'

], function (App) {
    document.navNetmapAppSpinner.stop(); // global spinner while javascript is loading it's dependencies
    define.amd.jQuery = true;

    // The "app" dependency is passed in as "App"
    // Again, the other dependencies passed in are not "AMD" therefore don't pass a parameter to this function
    App.initialize();
});

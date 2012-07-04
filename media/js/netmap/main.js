
// Require.js configure shortcut aliases
require.config({
    paths: {
        //loader: 'libs/backbone/loader',
        jQuery: 'libs/jquery/jquery',
        jQueryUI: '../jquery-ui-1.8.21.custom.min',
        Underscore: 'libs/underscore/underscore',
        Handlebars: 'libs/handlebars/handlebars',
        Backbone: 'libs/backbone/backbone',

        /*text: 'libs/require/text',
         order: 'libs/require/order',*/
        Netmap: '../netmap',
        templates: 'templates'
    }
});

require([
    // Load our app module and pass it to our definition function
    'app',
    // Some plugins have to be loaded in order due to their non AMD compliance
    // Because these scripts are not "modules" they do not pass any values to the definition function below
    'order!libs/jquery/jquery-full',
    'order!../jquery-ui-1.8.21.custom.min',
    'order!libs/underscore/underscore-full',
    'order!libs/handlebars/handlebars-full',
    'order!libs/backbone/backbone-full'

], function(App) {
    // The "app" dependency is passed in as "App"
    // Again, the other dependencies passed in are not "AMD" therefore don't pass a parameter to this function
    App.initialize();
});
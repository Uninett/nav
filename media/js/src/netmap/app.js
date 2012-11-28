define([
    'plugins/header_footer_minimize',
    'netmap/router', // Request router.js
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/handlebars'
], function(PluginHeaderFooter, Router) {
    var initialize = function () {
        var IESanityTest = {
            Version: function() {
                var version = 666; // assume good
                if (navigator.appVersion.indexOf("MSIE") != -1) {
                    version = parseFloat(navigator.appVersion.split("MSIE")[1]);
                }
                return version;
            },
            DocumentVersion: function () {
                var version = 666; // assume good
                if (navigator.appVersion.indexOf("MSIE") != -1) {
                    var documentVersion = document.documentMode;
                    if (documentVersion !== undefined) {
                        version = documentVersion
                    } else {
                        version = 1; // documentMode included from IE8>=, just fail older browser!
                    }
                }
                return version;
            }
        };
        if (IESanityTest.Version() < 9) {
            alert("Your version of Internet Explorer is too old to run Netmap. Please upgrade to IE9 or make sure DocumentMode is set to 9 or newer");
        } else if (IESanityTest.DocumentVersion() < 9) {
            alert("Netmap requires Internet Explorer to have DocumentMode 9 or newer!");
        }

        // Comment this one out when moving to mod_wsgi! mod_python
        // does not support PUT etc , only GET and POST. Silly mod_python!
        Backbone.emulateHTTP = true;

        var headerFooterPlugin = new PluginHeaderFooter();

        headerFooterPlugin.initialize({
            'header': { el: $('#header'), hotkey: { altKey: false, ctrlKey: true, shiftKey: true, charCode: 6} },
            'footer': { el: $('#footer'), hotkey: { altKey: false, ctrlKey: true, shiftKey: true, charCode: 6} }
        });

        Handlebars.registerHelper('capitalize', function (type) {
            return type.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
        });

        Handlebars.registerHelper('uppercase', function (type) {
            if (typeof type == 'string' || type instanceof String) {
                return type.toUpperCase();
            } else {
                return type;
            }
        });

        //Backbone.emulateJSON = true;
        // Pass in our Router module and call it's initialize function
        Router.initialize();
    };

    return {
        initialize: initialize
    };
});
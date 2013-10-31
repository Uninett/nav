define([
    'plugins/header_footer_minimize',
    'plugins/netmap-extras',
    'netmap/router', // Request router.js
    'netmap/resource',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/handlebars'
], function(PluginHeaderFooter, NetmapExtras, Router, Resource) {
    var initialize = function () {
        $.browser.chrome = /chrome/.test(navigator.userAgent.toLowerCase());

        var IESanityTest = {
            Version: function() {
                var version = 666; // assume good
                if (navigator.appVersion.indexOf("MSIE") !== -1) {
                    version = parseFloat(navigator.appVersion.split("MSIE")[1]);
                }
                return version;
            },
            DocumentVersion: function () {
                var version = 666; // assume good
                if (navigator.appVersion.indexOf("MSIE") !== -1) {
                    var documentVersion = document.documentMode;
                    if (documentVersion !== undefined) {
                        version = documentVersion;
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

        Resource.initialize();

        // Comment this one out when moving to mod_wsgi! mod_python
        // does not support PUT etc , only GET and POST. Silly mod_python!
//        Backbone.emulateHTTP = true;

        var headerFooterPlugin = new PluginHeaderFooter();

        headerFooterPlugin.initialize({
            'header': { el: $('#header'), hotkey: { altKey: false, ctrlKey: true, shiftKey: true, charCode: 6} },
            'footer': { el: $('#footer'), hotkey: { altKey: false, ctrlKey: true, shiftKey: true, charCode: 6} }
        });

        Handlebars.registerHelper('capitalize', function (type) {
            return type.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
        });

        Handlebars.registerHelper('uppercase', function (type) {
            if (typeof type === 'string' || type instanceof String) {
                return type.toUpperCase();
            } else {
                return type;
            }
        });

        Handlebars.registerHelper('toLowerCase', function (value) {
            return (value && typeof value === 'string') ? value.toLowerCase() : '';
        });

        Handlebars.registerHelper('eachkeys', function(context, options) {
            var fn = options.fn, inverse = options.inverse;
            var ret = "";

            var empty = true;
            for (var key in context) { empty = false; break; }

            if (!empty) {
                for (key in context) {
                    ret = ret + fn({ 'key': key, 'value': context[key]});
                }
            } else {
                ret = inverse(this);
            }
            return ret;
        });

        Handlebars.registerHelper('ifequal', function (val1, val2, fn, elseFn) {
            if (val1 === val2) {
                return fn();
            }
            else if (elseFn) {
                return elseFn();
            }
        });

        Handlebars.registerHelper('round', function (value) {
            return (value && typeof value === 'number') ? Math.round(value) : 0;
        });

        // Same as each, just including index
        Handlebars.registerHelper('iter', function (context, options) {
            var fn = options.fn, inverse = options.inverse;
            var ret = "";

            if (context && context.length > 0) {
                for (var i = 0, j = context.length; i < j; i++) {
                    ret = ret + fn(_.extend({}, context[i], { percent: context.length - 1 - i, isDecade: i % 10 === 0 }));
                }
            } else {
                ret = inverse(this);
            }
            return ret;
        });

        Handlebars.registerHelper("traffic_si", function (value) {
            return NetmapExtras.convert_bits_to_si(value);
        });

        Handlebars.registerHelper("debug", function (optionalValue) {
            console.log("\nCurrent Context");
            console.log("====================");
            console.log(this);

            if (arguments.length > 1) {
                console.log("Value");
                console.log("====================");
                console.log(optionalValue);
            }
        });

        Backbone.Model.extend({
            toJSON: function () {
                var clone = _.clone(this.attributes);
                _.each(clone, function (attr, idx) {
                    if (attr.toJSON) {
                        clone[idx] = attr.toJSON();
                    }
                });
                return clone;
            }
        });

        Backbone.View.prototype.attachSubView = function (view, ViewClass, viewOptions) {
            if (!!viewOptions && !_.isObject(viewOptions)) {
                viewOptions = {
                    el: $(viewOptions, this.$el)
                };
            }

            if (view) {
                if (view.options) {
                    _.extend({}, view.options, viewOptions);
                }
                view.setElement(viewOptions.el);
            } else {
                view = new ViewClass(viewOptions);
            }
            if (typeof view.initWidget === "function") {
                view.initWidget(viewOptions);
            }
            view.render();
            return view;
        };

        //Backbone.emulateJSON = true;
        // Pass in our Router module and call it's initialize function
        Router.initialize();
    };

    return {
        initialize: initialize
    };
});

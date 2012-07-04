
define([
    'jQuery',
    'Underscore',
    'Backbone',
    'router' // Request router.js
], function($, _, Backbone, Router, posts) {
    var initialize = function () {
        self = this;
        // Pass in our Router module and call it's initalize function
        Router.initialize();
    };

    return {
        initialize: initialize
    };
});
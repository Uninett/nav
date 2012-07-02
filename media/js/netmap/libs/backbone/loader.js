define(['order!libs/jquery/jquery-full', 'order!libs/underscore/underscore-full', 'order!libs/handlebars/handlebars-full', 'order!libs/backbone/backbone-full'],
    function(){
        var libs= {
            Backbone: Backbone.noConflict(),
            _: _.noConflict(),
            $: jQuery.noConflict(),
            Handlebars: Handlebars
        };
        return libs;
    });
define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/navigation.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, netmapTemplate) {

    var NavigationView = Backbone.View.extend({
        events: {
                'click #toggle_view' : 'toggleView'
        },
        initialize: function () {
            console.log("foodsfsdfbar");
            this.isContentVisible = true;


            this.template = Handlebars.compile(netmapTemplate);

            // Registers Handlebars helpers

            Handlebars.registerHelper('eachkeys', function(context, options) {
                var fn = options.fn, inverse = options.inverse;
                var ret = "";

                var empty = true;
                for (key in context) { empty = false; break; }

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

            // Bindings

            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);

        },
        render: function () {
            var self = this;

            var context = {
                'link_types': {
                    '2':  false,
                    '2v': false,
                    '3':  false
                },
                'categories' : ['SW', 'R']
            };
            // Might be a new view, so no link_types is selected!
            if (this.model.attributes.link_types !== undefined) {
                for (var i = 0; i < this.model.attributes.link_types.length; i++) {
                    var selected_linktype = this.model.attributes.link_types[i];
                    context.link_types[selected_linktype] = true;
                }
            } // default to layer2 maybe?

            var out = this.template({ model: context});
            this.$el.html(out);

            return this;
        },
        toggleView: function (e) {
            var $helper = $(this.$el.parent());
            var $helper_content = $(".inner_wrap", this.$el);

            var margin;

            if (!this.isContentVisible) {
                margin = 170;

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin-40) }, 400);

                $("a#toggle_view", this.$el).html("&lt;&lt;");

            } else {
                margin = 30;
                $helper.animate({'width': "{0}px".format(12) }, 400);
                $helper_content.fadeOut('fast');

                $("a#toggle_view", this.$el).html("&gt;&gt;");

            }

            $("#netmap_main_view").animate({'margin-left': "{0}px".format(margin)}, 400);

            this.isContentVisible = !this.isContentVisible;
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NavigationView;
});






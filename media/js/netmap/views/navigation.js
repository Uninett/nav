define([
    'jquery',
    'underscore',
    'backbone',
    'backbone_eventbroker',
    'handlebars',
    'netmapextras',
    'text!templates/navigation.html'

], function ($, _, Backbone, BackboneEventbroker, Handlebars, NetmapHelpers, netmapTemplate) {

    var NavigationView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            'click #toggle_view':      'toggleView',
            'click input[type=radio]': 'onRadioLayerClick',
            'click input[name="categories[]"]': 'onCheckboxLayerClick',
            'click input[name="filter_orphans"]': 'onFilterOrphansClick',
            'click input[name="group_roomid"]': 'onGroupByRoomClick',
            'click input[name="freezeNodes"]': 'onFreezeNodesClick'
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
                    'layer2':  false,
                    'layer3':  false
                },
                // eew, should get available categories from app context somehow
                // ie, load categories list on app start..
                'categories': {
                    'GSW':   false,
                    'GW':    false,
                    'SW':    false,
                    'OTHER': false,
                    'WLAN':  false,
                    'SRV':   false,
                    'EDGE':  false,
                    'ELINK': false
                },
                'specific_filters': {
                    'groupby_room': false
                }
            };

            for (var i = 0; i < this.model.attributes.categories.length; i++) {
                var category = this.model.attributes.categories[i];
                context.categories[category] = true;
            }

            context.link_types[NetmapHelpers.topology_id_to_topology_link(this.model.attributes.topology)] = true;

            var out = this.template({ model: context});
            this.$el.html(out);

            self.alignView();

            return this;
        },
        alignView: function () {
            var $helper = $(this.$el.parent());
            var $helper_content = $(".inner_wrap", this.$el);

            var margin;

            if (!this.isContentVisible) {
                margin = 30;
                $helper.animate({'width': "{0}px".format(12) }, 400);
                $helper_content.fadeOut('fast');

                $("a#toggle_view", this.$el).html("&gt;&gt;");

            } else {
                margin = 170;

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin-40) }, 400);

                $("a#toggle_view", this.$el).html("&lt;&lt;");

            }

            return margin;
            //$("#netmap_main_view").animate({'margin-left': "{0}px".format(margin)}, 400);

        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();
            this.broker.trigger('map:resize:animate', {marginLeft: margin});
        },
        onRadioLayerClick: function (e) {
            e.stopPropagation();

            this.model.set({topology: NetmapHelpers.topology_link_to_id($(e.currentTarget).val())});
            this.broker.trigger('map:topology_change', this.model.get('topology'));
            //NetmapHelpers.topology_link_to_id($e.currentTarget).val());
        },
        onCheckboxLayerClick: function (e) {
            // jQuery<=1.6
            var categories = this.model.get('categories');
            if (!$(e.currentTarget).prop('checked')) {
                for (var i = 0; i < categories.length; i++) {
                    var category = categories[i];
                    if (category.toLowerCase() === $(e.currentTarget).val().toLowerCase()) {
                        categories.splice(i, 1);
                        break;
                    }
                }
            } else {
                categories.push($(e.currentTarget).val());
            }
            this.model.set({ categories: categories});

            this.broker.trigger('map:redraw');
        },
        onFilterOrphansClick: function (e) {
            this.broker.trigger('map:redraw', {
                filter_orphans: $(e.currentTarget).prop('checked')
            });
        },
        onGroupByRoomClick: function (e) {
            this.broker.trigger('map:redraw', {
                groupby_room: $(e.currentTarget).prop('checked')
            });
        },
        onFreezeNodesClick: function (e) {
            this.broker.trigger('map:freezeNodes', $(e.currentTarget).prop('checked'));
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NavigationView;
});






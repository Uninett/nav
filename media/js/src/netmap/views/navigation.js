define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/navigation.html',
    'netmap/collections/traffic_gradient',
    'netmap/views/modal/traffic_gradient',
    'netmap/views/layer_toggler',
    'netmap/views/categories_toggler',
    'netmap/views/orphans_toggler',
    'netmap/views/position_toggler',
    'netmap/views/algorithm_toggler',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, netmapTemplate, TrafficGradientCollection, TrafficGradientView, LayerView, CategoryView, OrphanView, PositionView, AlgorithmView) {

    var NavigationView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest',
            'map:loading:done': 'eventLoadingDone',
            'map:topology_change:loading': 'setLoading'
        },
        events: {
            'click #toggle_view':      'toggleView',
            'click input[name="mouseOver[]"]': 'onUIMouseOverClick',
            'click input[name="topologyErrors"]': 'onUITopologyErrorsClick',
            'click input[name="nodesFixed"]': 'onNodesFixedClick',
            'click input[name="trafficGradient"]': 'onTrafficGradientClick'
        },
        initialize: function () {
            this.gradientView = null;
            this.categoriesView = null;
            this.orphansView = null;
            this.positionView = null;

            this.isContentVisible = true;
            this.broker.register(this);

            _.bindAll(this, 'on_keypress');
            $(document).bind('keypress', this.on_keypress);

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

            this.context = {
                'link_types': {
                    'layer2':  false,
                    'layer3':  false
                },
                // eew, should get available categories from app context somehow
                // ie, load categories list on app start..
               'specific_filters': {
                    'position': {
                        'none':     false,
                        'room':     false,
                        'location': false
                    },
                },
                'ui': {
                    'mouseover': {
                        'nodes': { state: false, hotkey: 'n' },
                        'links': { state: false, hotkey: 'l' }
                    },
                    'topology_errors': false,
                    'freezeNodes': false
                }
            };
            this.isLoading = !!(this.options.isLoading);

            this.layer_toggler = null;

        },
        setLoading: function (state) {
            this.isLoading = state;
            this.render();
        },
        eventLoadingDone: function () {
            this.isLoading = false;
            this.render();
        },
        render: function () {
            var self = this;

            var out = this.template({ model: this.context, isVisible: this.isContentVisible, isLoading: this.isLoading });
            this.$el.html(out);

            if (this.layer_toggler) {
                this.layer_toggler.close();
            }

            if (this.layer_toggler) {
                this.layer_toggler.setElement($('#layer_view', this.$el));
                this.layer_toggler.render();
            } else {
                this.layer_toggler = new LayerView({el: $('#layer_view', this.$el)}).render();
            }

            if (this.categoriesView) {
                this.categoriesView.close();
            }

            if (this.categoriesView) {
                this.categoriesView.setElement($('#categories_view', this.$el));
                this.categoriesView.render();
            } else {
                this.categoriesView = new CategoryView({el: $('#categories_view', this.$el)}).render();
            }

            if (this.orphansView) {
                this.orphansView.setElement($('#orphan_view', this.$el));
                this.orphansView.render();
            } else {
                this.orphansView = new OrphanView({el: $('#orphan_view', this.$el)});
            }

            if (this.positionView) {
                this.positionView.setElement($('#position_view', this.$el));
                this.positionView.render();
            } else {
                this.positionView = new PositionView({el: $('#position_view', this.$el)});
            }

            new AlgorithmView({el: $('#algorithm_view', this.$el)}).render();

            return this;
        },
        alignView: function () {
            var $helper = $(this.$el.parent());
            var $helper_content = $(".inner_wrap.left_sidebar");

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
        headerFooterMinimizeRequest: function (options) {
            if (options && options.name === 'header' && (options.isShowing !== this.isContentVisible)) {
                this.toggleView();
            }
        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();
            this.broker.trigger('map:resize:animate', {marginLeft: margin});
        },
        onUIMouseOverClick: function (e) {
            this.context.ui.mouseover[$(e.currentTarget).val()].state = $(e.currentTarget).prop('checked');
            this.broker.trigger('map:ui:mouseover:'+$(e.currentTarget).val(), $(e.currentTarget).prop('checked'));
            //this.render();
        },
        onUITopologyErrorsClick: function (e) {
            this.context.ui.topology_errors = $(e.currentTarget).prop('checked');
            this.broker.trigger('map:redraw', {
                topologyErrors: $(e.currentTarget).prop('checked')
            });
        },
        onNodesFixedClick: function (e) {
            var val = $(e.currentTarget).val();
            if (val === 'Fix') {
                this.broker.trigger('map:fixNodes', true);
            } else if (val === 'UnFix') {
                this.broker.trigger('map:fixNodes', false);
            }
        },
        onTrafficGradientClick: function (e) {
            var self = this;
            if (this.gradientView) {
                this.gradientView.close();
            }

            var gradientModel = new TrafficGradientCollection();
            gradientModel.fetch({
                success: function (model) {
                    self.gradientView = new TrafficGradientView({collection: model});
                    self.gradientView.render();
                }
            });

        },
        on_keypress: function (e) {
            if (e.charCode === 110) { // n
                this.context.ui.mouseover.nodes.state = !this.context.ui.mouseover.nodes.state;
                this.broker.trigger('map:ui:mouseover:nodes', this.context.ui.mouseover.nodes.state);
            } else if (e.charCode === 108) { // l
                this.context.ui.mouseover.links.state = !this.context.ui.mouseover.links.state;
                this.broker.trigger('map:ui:mouseover:links', this.context.ui.mouseover.links.state);
            }
            this.render();
        },
        close:function () {
            this.layer_toggler.close();
            $(document).unbind('keypress', 'on_keypress');
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NavigationView;
});






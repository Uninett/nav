define([
    'netmap/views/widget_mixin',
    'netmap/collections/checkradio',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Collection, Model, Template) {
    var MouseOverView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="mouseOver[]"]': 'setMouseOverOptions'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);
            _.bindAll(this, 'onKeypress');
            $(document).bind('keypress', this.onKeypress);

            if (!this.collection) {
                this.collection = new Collection([
                    {name: "nodes"},
                    {name: "links"}
                ]);
            }

            this.collection.bind("change", this.broadcastMouseOverFilters, this);

            return this;
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Mouseover',
                    title_help: 'Automatically select node or link when mouse pointer is over it',
                    type: 'checkbox',
                    identifier: 'mouseOver',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
                })
            );

            return this;
        },
        broadcastMouseOverFilters: function () {
            this.broker.trigger("netmap:changeMouseOverFilters", this.collection);
        },
        setMouseOverOptions: function (e) {
            var itemInCollection = this.collection.get($(e.currentTarget).val());
            if (itemInCollection) {
                itemInCollection.set('is_selected', $(e.currentTarget).prop('checked'));

                this.broker.trigger('netmap:ui:mouseover', itemInCollection);
            }
            // render not needed.. done by browser.
        },
        onKeypress: function (e) {
            var itemInCollection = null;
            if (e.charCode === 110) { // n
                itemInCollection = this.collection.get('nodes');
            } else if (e.charCode === 108) { // l
                itemInCollection = this.collection.get('links');
            }
            if (itemInCollection) {
                itemInCollection.set("is_selected", !itemInCollection.get("is_selected"));
                this.broker.trigger('netmap:ui:mouseover', itemInCollection);
                this.render();
            }
        },

        close:function () {
            this.broker.unregister(this);
            $(document).unbind('keypress', 'onKeypress');
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return MouseOverView;
});

define([
    'netmap/collections/checkradio',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Model, Template) {
    var MouseOverView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="mouseOver[]"]': 'setMouseOverOptions'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);

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
                    title_help: 'Enable &quot;auto clicking&quot; when hovering a node or a link',
                    type: 'checkbox',
                    identifier: 'mouseOver',
                    collection: this.collection.toJSON()
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
                itemInCollection.is_selected = $(e.currentTarget).prop('checked');
                //this.broker.trigger('map:ui:mouseover:'+$(e.currentTarget).val(), $(e.currentTarget).prop('checked'));
            }

            //this.render();
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return MouseOverView;
});

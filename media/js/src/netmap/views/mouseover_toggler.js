define([
    'netmap/collections/categories',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/categories_toggler.html',
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
            // todo: fetch collection from api.
            if (!this.collection) {
                this.collection = new Collection([
                    {name: "GSW"},
                    {name: "GW"},
                    {name: "SW"},
                    {name: "OTHER"},
                    {name: "WLAN"},
                    {name: "SRV"},
                    {name: "EDGE"},
                    {name: "ELINK", 'is_selected': false}
                ]);
            }

            this.collection.bind("change", this.broadcastcategoriesFilters, this);
            //this.model.bind("change:layer", this.updateSelection, this);
            //this.model.bind("change", this.render, this);

            return this;
        },

        render: function () {
            this.$el.html(
                this.template({collection: this.collection.toJSON()})
            );

            return this;
        },
        broadcastcategoriesFilters: function () {
            this.broker.trigger("netmap:changeCategoriesFilters", this.collection);
        },
        setMouseOverOptions: function (e) {
            this.context.ui.mouseover[$(e.currentTarget).val()].state = $(e.currentTarget).prop('checked');
            this.broker.trigger('map:ui:mouseover:'+$(e.currentTarget).val(), $(e.currentTarget).prop('checked'));
            //this.render();
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return MouseOverView;
});

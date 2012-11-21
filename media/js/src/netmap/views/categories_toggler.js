define([
    'netmap/collections/categories',
    'netmap/models/category',
    'libs-amd/text!netmap/templates/categories_toggler.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Model, Template) {
    var CategoriesView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="categories[]"]': 'updateFilters'
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
        updateFilters: function (e) {
            // jQuery<=1.6
            var categoryToUpdate = null;
            categoryToUpdate = this.collection.get($(e.currentTarget).val().toUpperCase());
            if (categoryToUpdate) {
                // category found!
                categoryToUpdate.set({'is_selected': $(e.currentTarget).prop('checked')});
            }

            this.broker.trigger('map:redraw');
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return CategoriesView;
});

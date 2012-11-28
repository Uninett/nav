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
    var CategoriesView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="categories[]"]': 'updateFilters'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);
            // todo: fetch collection from api.
            if (!this.collection) {
                // also see map model file!
                this.collection = new Collection([
                    {name: "GSW", 'is_selected': true},
                    {name: "GW", 'is_selected': true},
                    {name: "SW", 'is_selected': true},
                    {name: "OTHER", 'is_selected': true},
                    {name: "WLAN", 'is_selected': true},
                    {name: "SRV", 'is_selected': true},
                    {name: "EDGE",'is_selected': true},
                    {name: "ELINK"}
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

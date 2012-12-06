define([
    'netmap/collections/categories',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Model, Template) {
    var CategoriesView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        interests: {
            "netmap:changeMapProperties": "updateFiltersFromBroadcast"
        },
        events: {
            'click input[name="categories[]"]': 'updateFilters'
        },
        initialize: function () {
            this.broker.register(this);
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
                this.template({
                    title: 'Categories',
                    type: 'checkbox',
                    identifier: 'categories',
                    nameInUppercase: true,
                    collection: this.collection.toJSON()
                })
            );

            return this;
        },
        broadcastcategoriesFilters: function () {
            this.broker.trigger("netmap:changeCategoriesFilters", this.collection);
            this.render();
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
        updateFiltersFromBroadcast: function (mapProperties) {
            this.collection.forEach(function (model) {
                model.set({'is_selected': false}, {'silent': true});
            });

            // set's is_selected true on categories mentioned in mapProperties.categories which is in this.collection
            _.invoke(this.collection.filter(function (model) {
                return _.contains(mapProperties.get('categories').pluck('name'), model.get('name'));
            }), "set", {'is_selected': true});

            this.render();
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return CategoriesView;
});

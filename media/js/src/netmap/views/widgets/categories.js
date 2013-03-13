define([
    'netmap/resource',
    'netmap/collections/categories',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Resources, Collection, Model, Template) {
    var CategoriesView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeMapProperties": "updateFiltersFromBroadcast",
            "netmap:setMapProperties:done": "updateFiltersFromBroadcast"
        },
        events: {
            'click input[name="categories[]"]': 'updateFilters'
        },
        initialize: function () {
            var self = this;
            this.broker.register(this);
            this.template = Handlebars.compile(Template);

            if (!this.model) {
                this.model = Resources.getActiveMapModel();

                var missingDjangoCategoriesModels = _.reject(Resources.getAvailableCategories(), function (r) {
                    return self.model.get('categories').find(function (c) {
                        return c.get('name') === r.pk;
                    });
                });

                _.each(missingDjangoCategoriesModels, function (m) {
                    self.model.get('categories').add({name: m.pk, is_selected: false});
                });

            }

            this.model.get("categories").bind("change", this.render, this);
            this.model.get("categories").each(function(category){
                category.bind("change", function(){ self.trigger("change:categories:" + category.id, category) });
            });

            return this;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Categories',
                    type: 'checkbox',
                    identifier: 'categories',
                    nameInUppercase: true,
                    collection: this.model.get('categories').toJSON(),
                    isViewEnabled: this.isViewEnabled
                })
            );

            return this;
        },
        updateFilters: function (e) {
            // jQuery<=1.6
            var categoryToUpdate = null;
            categoryToUpdate = this.model.get('categories').get($(e.currentTarget).val().toUpperCase());
            if (categoryToUpdate) {
                // category found!
                categoryToUpdate.set({'is_selected': $(e.currentTarget).prop('checked')});
            }
        },
        updateFiltersFromBroadcast: function (mapProperties) {
            this.model.set('categories', mapProperties.get('categories'));

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

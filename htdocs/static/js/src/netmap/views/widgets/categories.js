define([
    'netmap/views/widget_mixin',
    'netmap/resource',
    'netmap/collections/categories',
    'netmap/models/input_checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Resources, Collection, Model, Template) {
    var CategoriesView = Backbone.View.extend(
        _.extend({}, WidgetMixin, {
        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeActiveMapProperty": "updateFiltersFromBroadcast"
        },
        events: {
            'click div.header': 'toggleWidget',
            'click input[name="categories[]"]': 'updateFilters'
        },
        initialize: function () {
            var self = this;
            this.broker.register(this);
            this.template = Handlebars.compile(Template);

            if (!this.model) {
                this.model = Resources.getActiveMapModel();
                this.addMissingDjangoCategoriesModels();
            }

            this.model.get("categories").bind("change", this.render, this);
            this.model.get("categories").each(function(category){
                category.bind("change", function(){ self.trigger("change:categories:" + category.id, category); });
            });

            return this;
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Categories',
                    type: 'checkbox',
                    identifier: 'categories',
                    nameInUppercase: true,
                    collection: this.model.get('categories').toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
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
            return true;
        },
        addMissingDjangoCategoriesModels: function () {
            var self = this;
            var missingDjangoCategoriesModels = _.reject(Resources.getAvailableCategories(), function (r) {
                return self.model.get('categories').find(function (c) {
                    return c.get('name') === r.pk;
                });
            });

            _.each(missingDjangoCategoriesModels, function (m) {
                self.model.get('categories').add({name: m.pk, is_selected: false});
            });
        },
        updateFiltersFromBroadcast: function (mapProperties) {
            this.model = mapProperties;
            this.addMissingDjangoCategoriesModels();
            this.render();
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return CategoriesView;
});

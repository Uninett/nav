define([
    'netmap/resource',
    'netmap/collections/categories',
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/default_map',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function(Resources, CategoriesCollection, MapCollection, MapPropertiesModel, DefaultMapModel) {

    function checkDefaultMapSetByAdministrator() {
        var self = this;
        // todo add a map the administrator can set to be default view
        // for every page request not containing a map id

        new DefaultMapModel().fetch({
            success: function (model, attributes) {
                self.setFavoriteView(model.get('viewid'));
                //Backbone.View.navigate("view/{0}".format(model.get('viewid')), true);
            },
            error: function () {
                self.setFavoriteView(null);
                // global not found, load UI and it will load default graph
                self.loadUi();
            }
        });

    }

    function checkDefaultMapForUser(userId) {
        var self = this;
        new DefaultMapModel({ownerid: userId}).fetch({
            success: function (model) {
                Resources.setFavoriteView(model.get('viewid'));
                //Backbone.View.navigate("view/{0}".format(model.get('viewid')), true);
            },
            error: function () {
                checkDefaultMapSetByAdministrator();
            }
        });
    }

    function findDefaultView() {
        var user_id = $("#netmap_userid").html();
        checkDefaultMapForUser(parseInt(user_id, 10));
    }


    var publicMethods = {
        initialize: function () {
            this.resources = {
                'graph': null,
                "activeMapModel": null,
                "mapCollection": null,
                'viewid': null,
                'favorite': null,
                'availableCategories': null
            };
            var self = this;

            var bootstrapMapPropertiesCollectionEl = $('#netmap_bootstrap_mapPropertiesCollection');
            var bootstrapIsFavoriteEl = $('#netmap_bootstrap_favoriteView');
            var bootstrapAvailableCategories = $('#netmap_bootstrap_availableCategories');

            try {
                if (bootstrapMapPropertiesCollectionEl) {
                    var bootstrapData = $.parseJSON(bootstrapMapPropertiesCollectionEl.text());

                    if (bootstrapData) {
                        self.resources.mapCollection = new MapCollection(MapCollection.prototype.parse(bootstrapData));
                    }
                } else {
                    this.resources.mapCollection = new MapCollection();
                }
                if (bootstrapIsFavoriteEl) {
                    var bootstrapDataFavorite = $.parseJSON(bootstrapIsFavoriteEl.text());
                    if (bootstrapDataFavorite) {
                        this.setFavoriteView(bootstrapDataFavorite.viewid);
                    }
                }

                if (bootstrapAvailableCategories) {
                    var data = $.parseJSON(bootstrapAvailableCategories.text());
                    if (data) {
                        this.resources.availableCategories = data;
                    }
                }
            } catch (SyntaxError) {
                if (!!console.log) {
                  console.log("Error parsing JSON bootstrap data probably, should not happen!");
                }
                throw SyntaxError;
            }


        },
        getAvailableCategories: function () {
            return this.resources.availableCategories;
        },
        getActiveMapModel: function () {
            return this.resources.activeMapModel;
        },
        getMapCollection: function () {
            return this.resources.mapCollection;
        },
        getMapByViewId: function (viewid) {
            return this.resources.mapCollection.get(viewid);
        },
        setViewId: function (viewid) {
            this.resources.viewid = viewid;
            if (!viewid) {
                this.resources.mapCollection.unshift({});
                this.resources.activeMapModel = this.resources.mapCollection.at(0);
            } else {
                this.resources.activeMapModel = this.resources.mapCollection.get(viewid);
            }
        },
        setFavoriteView: function (viewid) {
            this.resources.mapCollection.setFavorite(viewid);
        }

    };

    return publicMethods;
});
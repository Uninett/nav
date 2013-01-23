define([
    'netmap/collections/categories',
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/default_map',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function(CategoriesCollection, MapCollection, MapPropertiesModel, DefaultMapModel) {

    var self = this;

    var resources = {
    };

    var listeners = {
        'graph': [],
        'mapProperties': []
    };

    /*var broker = Backbone.EventBroker;
    broker.register(this);*/

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
                'mapProperties': null,
                'mapPropertiesCollection': null,
                'viewid': null,
                'favorite': null
            };
            var self = this;

            var bootstrapMapPropertiesCollectionEl = $('#netmap_bootstrap_mapPropertiesCollection');
            var bootstrapIsFavoriteEl = $('#netmap_bootstrap_favoriteView');

            if (bootstrapMapPropertiesCollectionEl) {
                var bootstrapData = $.parseJSON(bootstrapMapPropertiesCollectionEl.text());

                if (bootstrapData) {
                    self.resources.mapPropertiesCollection = new MapCollection(MapCollection.prototype.parse(bootstrapData));
                }
            } else {
                this.resources.mapPropertiesCollection = new MapCollection();
            }
            if (bootstrapIsFavoriteEl) {
                var bootstrapDataFavorite = $.parseJSON(bootstrapIsFavoriteEl.text());
                if (bootstrapDataFavorite) {
                    this.setFavoriteView(bootstrapDataFavorite.viewid);
                }
            }


            //findDefaultView();

        },
        getMapProperties: function () {
            return this.resources.mapProperties;
        },
        getMapPropertiesCollection: function () {
            return this.resources.mapPropertiesCollection;
        },
        getMapPropertiesByViewId: function (viewid) {
            return this.resources.mapPropertiesCollection.get(viewid);
        },
        setViewId: function (viewid) {
            this.resources.viewid = viewid;
            if (!viewid) {
                this.resources.mapPropertiesCollection.unshift({});
                this.resources.mapProperties = this.resources.mapPropertiesCollection.at(0);
            } else {
                this.resources.mapProperties = this.resources.mapPropertiesCollection.get(viewid);
            }
        },
        setFavoriteView: function (viewid) {
            this.resources.mapPropertiesCollection.setFavorite(viewid);
        }

    };

    return publicMethods;
});
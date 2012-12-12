define([
    'netmap/models/map',
    'libs/backbone'
], function (netmapModel) {
    var netmapCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/netmap',
        initialize: function () {

        },
        resetIsFavorite: function () {
            // Called before setIsFavorite in collection.
            this.each(function (element) {
                element.set({isFavorite: false}, {silent: true});
            });
        },
        setFavorite: function (model) {
            this.resetIsFavorite();
            var inCollection = this.get(model);
            if (inCollection) {
                inCollection.set({isFavorite: true});
            }
        }

    });

    return netmapCollection;
});
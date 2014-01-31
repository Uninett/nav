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
        resetIsSelected: function () {
            this.each(function (element) {
                element.set({"is_selected": false}, {silent: true});
            });
        },
        setFavorite: function (model) {
            this.resetIsFavorite();
            var inCollection = this.get(model);
            if (inCollection) {
                inCollection.set({isFavorite: true});
            }
        },
        getFavorite: function () {
            var target = this.where({isFavorite: true});
            if (_.size(target) === 1) { return target[0] ;}
            return null;
        },
        parse: function (resp) {

            _.each(resp, function (model) {
               model = netmapModel.prototype.parse(model);
            });
            return resp;
        }


    });

    return netmapCollection;
});

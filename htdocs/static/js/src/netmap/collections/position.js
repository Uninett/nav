define([
    'netmap/models/position',
    'libs/backbone'
], function (PositionModel) {
    var PositionCollection = Backbone.Collection.extend({
        model: PositionModel,
        initialize: function () {
        },
        setAllUnselectedSilently: function () {
            _.each(this.models, function (model) {
                model.set({is_selected: false}, {silent: true});

            });
        },
        has_targets: function () {
            var room = this.get("room");
            var location = this.get("location");
            return (room && room.get("is_selected")) || (location && location.get("is_selected"));
        }

    });

    return PositionCollection;
});
define([
    'netmap/models/vlan',
    'libs/backbone'
], function (vlanModel) {
    var vlanCollection = Backbone.Collection.extend({
        model: vlanModel,
        initialize: function () {

        },
        parse: function (resp) {
            var parsedVlans = [];
            _.each(resp, function (model) {
               parsedVlans.push(vlanModel.prototype.parse(model));
            });
            return parsedVlans;
        },
        comparator: function (item) {
            return item.get('vlan');
        }


    });

    return vlanCollection;
});

define([
    'libs/backbone'
], function () {
    var edgeModel = Backbone.Model.extend({
        defaults: {
        },
        initialize: function () {
        },
        toJSON: function () {
            var json = $.extend(true, {}, this.attributes);
            if (!!json.vlan) { // only set in L3
                json.vlan = json.vlan.toJSON();
            }
            json.source.netbox = json.source.netbox.toJSON();
            json.target.netbox = json.target.netbox.toJSON();
            return json;
        }

    });
    return edgeModel;

});

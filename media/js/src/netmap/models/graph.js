define([
    'libs/netmap-extras',
    'libs/backbone'
], function (NetmapExtras) {
    var graphModel = Backbone.Model.extend({
        defaults: {
                  topology: 1
        },
        initialize: function () {
        },
        url: function () {
            var base = 'api/graph/{0}'.format(NetmapExtras.topology_id_to_topology_link(this.attributes.topology));
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + this.id;
        }


    });
    return graphModel;

});
define([
    'libs/backbone'
], function () {
    var graphModel = Backbone.Model.extend({
        defaults: {
                  topology: 2
        },
        initialize: function () {
        },
        url: function () {
            var base = 'api/graph/layer{0}'.format(this.get('topology'));
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + this.get('id');
        }


    });
    return graphModel;

});
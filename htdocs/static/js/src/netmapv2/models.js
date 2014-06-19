define([
    'libs/jquery',
    'libs/underscore',
    'libs/backbone'
], function () {

    var Node = Backbone.Model.extend({
        idAttribute: 'id',

        initialize: function () {
            this.set('node', this.get('id'));
        }
    });

    var Link = Backbone.Model.extend({
    });

    var Vlan = Backbone.Model.extend({
        idAttribute: 'nav_vlan'
    });

    var NetmapView;

    return {
        Node: Node,
        Link: Link,
        Vlan: Vlan,
        NetmapView: NetmapView
    };
});
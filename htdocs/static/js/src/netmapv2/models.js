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

    var NetmapView = Backbone.Model.extend({
        idAttribute: 'viewid',

        defaults: {
            timestamp: new Date(), // Used for ??
            title: 'Unsaved view',
            description: '',
            is_public: true,
            is_user_default: false,
            topology: 2,
            zoom: '0,0;0.5',
            display_orphans: false,
            displayTopologyErrors: false,

            categories: [],

            // Properties that don't get saved
            refreshInterval: -1
        },

        url: function () {
            if (this.isNew()) {
                return 'views/create/';
            }
            return 'views/' + this.id + '/';
        },

        parse: function(data) {
            if (data.viewid === window.netmapData.defaultView) {
                data.is_user_default = true;
            }
            return data;
        }
    });

    return {
        Node: Node,
        Link: Link,
        Vlan: Vlan,
        NetmapView: NetmapView
    };
});
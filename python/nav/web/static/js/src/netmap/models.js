define([
    'libs/underscore',
    'libs/backbone'
], function () {

    /**
     * Models for Netmap
     */

    var Node = Backbone.Model.extend({
        idAttribute: 'id',

        initialize: function () {
            this.set('node', this.get('id'));
        }
    });

    var NodePositions = Backbone.Model.extend({
        idAttribute: 'viewid',
        defaults: {
            data: []
        },

        url: function () {
            return 'views/' + this.get('viewid') + '/nodepositions/update/';
        },

        save: function (attrs, options) {
            options = options || {};
            const csrfToken = $('#netmap-view-settings-form input[name="csrfmiddlewaretoken"]').val();

            options.headers = {
                ...options.headers,
                'X-CSRFToken': csrfToken
            }
            return Backbone.Model.prototype.save.call(this, attrs, options);
        }
    });

    var Link = Backbone.Model.extend({
        defaults: {
            traffic: {}
        }
    });

    var Vlan = Backbone.Model.extend({
        idAttribute: 'nav_vlan'
    });

    /**
     * Not to be confused with the 'view'-concept in backbone itself.
     * This is a data model which encapsulates a number of options and filters
     * over how the netmap topology graph is displayed.
     */
    var NetmapView = Backbone.Model.extend({
        idAttribute: 'viewid',

        defaults: {
            timestamp: new Date(),
            title: 'New view',
            description: '',
            is_public: true,
            is_user_default: false,
            topology: 2,
            zoom: '0,0;0.5',
            display_orphans: false,
            display_elinks: false,
            displayTopologyErrors: false,

            categories: [
                'GW', 'GSW', 'SW', 'EDGE', 'WLAN', 'SRV', 'OTHER', 'ENV', 'POWER'
            ],
            location_room_filter: ''
        },

        initialize: function () {

            if (this.get('display_elinks')) {
                this.get('categories').push('ELINK');
            }
        },

        url: function () {
            if (this.isNew()) {
                return 'views/create/';
            }
            return 'views/' + this.id + '/';
        }
    });

    return {
        Node: Node,
        NodePositions: NodePositions,
        Link: Link,
        Vlan: Vlan,
        NetmapView: NetmapView
    };
});

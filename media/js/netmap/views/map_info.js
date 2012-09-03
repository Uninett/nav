define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/map_info.html',
    'views/netbox_info',
    'views/link_info'
], function ($, _, Backbone, Handlebars, NetmapHelpers, mapInfoTemplate, NetboxInfoView, LinkInfoView) {

    var MapInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            'map:show_vlan': 'setSelectedVlan'
        },
        events: {
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(mapInfoTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });

            this.render();

        },
        swap_to_link: function (link) {
            if (this.netboxInfoView !== undefined) {
                this.netboxInfoView.reset();
            }
            this.linkInfoView.setLink(link, this.selected_vlan);
            this.linkInfoView.render();
        },
        swap_to_netbox: function (netbox) {
            if (this.linkInfoView !== undefined) {
                this.linkInfoView.reset();
            }
            this.netboxInfoView.setNode(netbox, this.selected_vlan);
            this.netboxInfoView.render();
        },
        setSelectedVlan: function (selected_vlan) {
            this.selected_vlan = selected_vlan;
        },
        render: function () {
            var self = this;
            var out = this.template();

            var netbox = null;
            var link = null;

            if (this.linkInfoView !== undefined && this.linkInfoView.link) {
                link = this.linkInfoView.link;
                this.linkInfoView.close();
            } else if (this.netboxInfoView !== undefined && this.netboxInfoView.node) {
                netbox = this.netboxInfoView.node;
                this.netboxInfoView.close();
            }

            this.$el.html(out);

            this.linkInfoView = new LinkInfoView({el: $("#linkinfo", this.$el)});
            this.netboxInfoView = new NetboxInfoView({el: $("#nodeinfo", this.$el)});
            if (netbox !== null) {
                this.swap_to_netbox(netbox);
            } else if (link !== null) {
                this.swap_to_link(link);
            }

            return this;
        },
        close: function () {
            this.linkInfoView.close();
            this.netboxInfoView.close();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return MapInfoView;
});






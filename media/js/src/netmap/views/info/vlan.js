define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/info/vlan.html',
    'libs/handlebars',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, netmapTemplate) {

    var VlanInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            "click .vlan": "showVlan"
        },
        initialize: function () {
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.vlans = this.options.vlans;
            this.selectedVLANObject = undefined;
        },
        render: function () {
            var self = this;

            if (self.vlans !== undefined && self.vlans) {
                // Mark selected vlan in metadata for template.
                if (self.selectedVLANObject !== undefined && self.selectedVLANObject) {
                    for (var i = 0; i < self.vlans.length; i++) {
                        var vlan = self.vlans[i];
                        vlan.is_selected = vlan.nav_vlan === self.selectedVLANObject.navVlanId;
                    }
                } else {
                    _.each(self.vlans, function (vlan) {
                        vlan.is_selected = false;
                    });
                }
                var out = this.template({ vlans: self.vlans, selectedVLANObject: self.selectedVLANObject});
                this.$el.html(out);
            } else {
                this.$el.empty();
            }

            return this;
        },
        setVlans: function (vlans) {
            this.vlans = vlans;
        },
        showVlan: function (e) {
            e.stopPropagation();
            this.selectedVLANObject = {
                navVlanId: $(e.currentTarget).data().navVlan,
                displayText: $(e.currentTarget).html()
            };
            this.broker.trigger('netmap:selectVlan', this.selectedVLANObject);
            this.render();
        },
        setSelectedVlan: function (selected_vlan) {
            this.selectedVLANObject = selected_vlan;
            this.render();
        },
        reset: function () {
            this.vlans = undefined;
            this.selectedVLANObject = undefined;
            this.broker.trigger('netmap:selectVlan', null);
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return VlanInfoView;
});
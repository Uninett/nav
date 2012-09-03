define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/info/vlan.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, netmapTemplate) {

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
            this.selected_vlan = undefined;
        },
        render: function () {
            var self = this;

            if (self.vlans !== undefined && self.vlans) {
                // Mark selected vlan in metadata for template.
                if (self.selected_vlan !== undefined && self.selected_vlan) {
                    for (var i = 0; i < self.vlans.length; i++) {
                        var vlan = self.vlans[i];
                        vlan.is_selected = vlan.nav_vlan === self.selected_vlan.navVlanId;
                    }
                } else {
                    _.each(self.vlans, function (vlan) {
                        vlan.is_selected = false;
                    });
                }
                var out = this.template({ vlans: self.vlans, selected_vlan: self.selected_vlan});
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
            console.log("showVlan");
            this.selected_vlan = {
                navVlanId: $(e.currentTarget).data().navVlan,
                displayText: $(e.currentTarget).html()
            };
            this.broker.trigger('map:show_vlan', this.selected_vlan);
            this.render();
        },
        setSelectedVlan: function (selected_vlan) {
            this.selected_vlan = selected_vlan;
        },
        reset: function () {
            this.vlans = undefined;
            this.selected_vlan = undefined;
            this.broker.trigger('map:show_vlan', null);
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return VlanInfoView;
});
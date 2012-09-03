define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/link_info.html'

], function ($, _, Backbone, Handlebars, NetmapExtras, netmapTemplate) {

    var LinkInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            "click .vlan": "showVlan"
        },
        initialize: function () {
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.link = this.options.link;
            /*this.model.bind("change", this.render, this);
             this.model.bind("destroy", this.close, this);*/

        },
        render: function () {
            var self = this;


            var inOctets, outOctets, inOctetsRaw, outOctetsRaw = "N/A";
            if (self.link !== undefined) {
                if (self.link.data.traffic['inOctets'] != null) {
                    inOctets = NetmapExtras.convert_bits_to_si(self.link.data.traffic['inOctets'].raw * 8);
                    inOctetsRaw = self.link.data.traffic['inOctets'].raw;
                } else {
                    inOctets = inOctetsRaw = 'N/A';
                }
                if (self.link.data.traffic['outOctets'] != null) {
                    outOctets = NetmapExtras.convert_bits_to_si(self.link.data.traffic['outOctets'].raw * 8);
                    outOctetsRaw = self.link.data.traffic['outOctets'].raw;
                } else {
                    outOctets = outOctetsRaw = 'N/A';
                }

                // Mark selected vlan in metadata for template.
                if (self.selected_vlan !== undefined) {
                    for (var i = 0; i < self.link.data.uplink.vlans.length; i++) {
                        var vlan = self.link.data.uplink.vlans[i];
                        if (vlan.nav_vlan === self.selected_vlan.navVlanId) {
                            vlan.is_selected = true;
                        } else {
                            vlan.is_selected = false;
                        }
                    }
                } else {
                    _.each(self.link.data.uplink.vlans, function (vlan) {
                        vlan.is_selected = false;
                    });
                }

                var out = this.template({link: self.link,
                    inOctets: inOctets,
                    inOctetsRaw: inOctetsRaw,
                    outOctets: outOctets,
                    outOctetsRaw: outOctetsRaw,
                    selected_vlan: this.selected_vlan
                });

                this.$el.html(out);
            } else {
                this.$el.empty();
            }

            return this;
        },
        showVlan: function (e) {
            e.stopPropagation();

            this.selected_vlan = {
                navVlanId: $(e.currentTarget).data().navVlan,
                displayText: $(e.currentTarget).html()
            };
            this.broker.trigger('map:show_vlan', this.selected_vlan.navVlanId);
            this.render();
        },
        reset: function () {
            this.link = undefined;
            this.selected_vlan = undefined;
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return LinkInfoView;
});






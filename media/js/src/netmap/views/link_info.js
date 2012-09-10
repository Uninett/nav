define([
    'plugins/netmap-extras',
    'netmap/views/info/vlan',
    'libs-amd/text!netmap/templates/link_info.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone'

], function (NetmapExtras, VlanInfoView, netmapTemplate) {

    var LinkInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,

        initialize: function () {
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.link = this.options.link;
            this.vlanView = new VlanInfoView();
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

                var out = this.template({link: self.link,
                    inOctets: inOctets,
                    inOctetsRaw: inOctetsRaw,
                    outOctets: outOctets,
                    outOctetsRaw: outOctetsRaw
                });

                this.$el.html(out);
                this.$el.append(this.vlanView.render().el);
                this.vlanView.delegateEvents();
            } else {
                this.$el.empty();
            }

            return this;
        },
        setLink: function (link, selected_vlan) {
            this.link = link;
            this.vlanView.setVlans(link.data.uplink.vlans);
            this.vlanView.setSelectedVlan(selected_vlan);
        },
        reset: function () {
            this.link = undefined;
            this.selected_vlan = undefined;
            this.vlanView.setVlans(undefined);
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return LinkInfoView;
});






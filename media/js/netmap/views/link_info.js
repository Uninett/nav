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

            var thiss_vlans = (self.link.data.uplink.vlans !== null ? self.link.data.uplink.vlans : 'none');
            var vlans = [];
            _.each(thiss_vlans, function (num, key) { vlans.push(num.vlan); }, vlans);

            var out = this.template({link: self.link,
                inOctets: inOctets,
                inOctetsRaw: inOctetsRaw,
                outOctets: outOctets,
                outOctetsRaw: outOctetsRaw,
                vlans: vlans});

            this.$el.html(out);
            return this;
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).empty();
        }
    });
    return LinkInfoView;
});






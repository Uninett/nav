define([
    'plugins/netmap-extras',
    'netmap/views/info/vlan',
    'libs-amd/text!netmap/templates/widgets/link_info.html',
    'netmap/collections/l3edges',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapExtras, VlanInfoView, netmapTemplate, L3EdgeCollection) {

    var LinkInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            "netmap:selectVlan": "setSelectedVlan"
        },
        events: {
                "click div.toggleUplink": 'toggleUplinkInfo'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.link = this.options.link;
            this.vlanView = new VlanInfoView();
        },
        hasLink: function () {
            return !!this.link;
        },
        render: function () {
            var self = this;


            var inOctets, outOctets, inOctetsRaw, outOctetsRaw = "N/A";
            if (self.link !== undefined) {
                inOctets = inOctetsRaw = outOctets = outOctetsRaw = 'N/A';


                var link =  {};
                _.each(self.link.data, function (data, key) { link[key] = data.toJSON(); });
                var context = {link: link,
                    inOctets: inOctets ,
                    inOctetsRaw: inOctetsRaw,
                    outOctets: outOctets,
                    outOctetsRaw: outOctetsRaw,
                    imagePath: NAV.imagePath
                };
                if (self.link.data.edges instanceof L3EdgeCollection) {
                    context.l3 = true;
                } else {
                    context.l2 = true;
                }
                var out = this.template(context);

                this.$el.html(out);
                this.$el.append(this.vlanView.render().el);
                this.vlanView.delegateEvents();
            } else {
                this.$el.empty();
            }

            return this;
        },
        toggleUplinkInfo: function (event) {
            var target = $(event.currentTarget);
            target.find("div.linkSource").toggle();
        },
        setSelectedVlan: function (selected_vlan) {
            this.vlanView.setSelectedVlan(selected_vlan);
            this.render();
        },
        setLink: function (link, selected_vlan) {
            this.link = link;
            this.vlanView.setVlans(link.data.vlans);
            this.vlanView.setSelectedVlan(selected_vlan);
            this.render();
        },
        reset: function () {
            this.link = undefined;
            this.selectedVLANObject = undefined;
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






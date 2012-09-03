define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/netbox_info.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, netmapTemplate) {

    var NetboxInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            "click .vlan": "showVlan",
            "click input[name=positionFixed]": 'notifyMap'
        },
        initialize: function () {
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.node = this.options.node;
            /*this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);*/

        },
        render: function () {
            var self = this;
            if (self.node !== undefined) {
                // Mark selected vlan in metadata for template.
                if (self.selected_vlan !== undefined) {
                    for (var i = 0; i < self.node.data.vlans.length; i++) {
                        var vlan = self.node.data.vlans[i];
                        vlan.is_selected = vlan.nav_vlan === self.selected_vlan.navVlanId;
                    }
                } else {
                    _.each(self.node.data.vlans, function (vlan) {
                        vlan.is_selected = false;
                    });
                }
                var out = this.template({ node: self.node, selected_vlan: self.selected_vlan});
                this.$el.html(out);
            } else {
                this.$el.empty();
            }

            return this;
        },
        notifyMap: function (e) {
            this.broker.trigger('map:node:fixed', {sysname: this.node.data.sysname, fixed: $(e.currentTarget).prop('checked')});
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
            this.node = undefined;
            this.selected_vlan = undefined;
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NetboxInfoView;
});






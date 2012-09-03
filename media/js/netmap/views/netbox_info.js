define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'views/info/vlan',
    'text!templates/netbox_info.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, VlanInfoView, netmapTemplate) {

    var NetboxInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            "click input[name=positionFixed]": 'notifyMap'
        },
        initialize: function () {
            this.template = Handlebars.compile(netmapTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });
            this.node = this.options.node;
            this.vlanView = new VlanInfoView();

        },
        render: function () {
            var self = this;
            if (self.node !== undefined) {
                var out = this.template({ node: self.node });
                this.$el.html(out);
                this.$el.append(this.vlanView.render().el);
                this.vlanView.delegateEvents();
            } else {
                this.$el.empty();
            }

            return this;
        },
        setNode: function (node, selected_vlan) {
            this.node = node;
            this.vlanView.setVlans(this.node.data.vlans);
            this.vlanView.setSelectedVlan(selected_vlan);
        },
        setSelectedVlan: function (vlan) {
            this.vlanView.setSelectedVlan(vlan);
        },
        notifyMap: function (e) {
            this.broker.trigger('map:node:fixed', {sysname: this.node.data.sysname, fixed: $(e.currentTarget).prop('checked')});
        },
        reset: function () {
            this.node = undefined;
            this.render();
        },
        close: function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NetboxInfoView;
});






define([
    'plugins/netmap-extras',
    'netmap/views/info/vlan',
    'libs-amd/text!netmap/templates/widgets/netbox_info.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, VlanInfoView, netmapTemplate) {

    var NetboxInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            "netmap:selectVlan": "setSelectedVlan"
        },
        events: {
            "click input[name=positionFixed]": 'notifyMap'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(netmapTemplate);
            this.node = this.options.node;
            this.vlanView = new VlanInfoView();
        },
        render: function () {
            var self = this;
            if (!!self.node) {
                var nodeJson = self.node.toJSON();
                nodeJson.fixed = !!self.node.fixed;
                var out = this.template({
                    'node': nodeJson,
                    'isElink': !!self.node.get('category') && self.node.get('category') === 'elink',
                    'isWidgetVisible': !!this.options.isWidgetVisible,
                    imagePath: NAV.imagePath
                });
                this.$el.html(out);
                this.$el.append(this.vlanView.render().el);
                this.vlanView.delegateEvents();
            } else {
                this.$el.empty();
            }

            return this;
        },
        hasNode: function () {
            return !!this.node;
        },
        setNode: function (node, selected_vlan) {
            this.node = node;
            this.vlanView.setVlans(this.node.get('vlans'));
            this.vlanView.setSelectedVlan(selected_vlan);
            this.render();
        },
        setSelectedVlan: function (vlan) {
            this.vlanView.setSelectedVlan(vlan);
        },
        notifyMap: function (e) {
            this.broker.trigger('netmap:node:setFixed', {
                sysname: this.node.get('sysname'),
                fixed: $(e.currentTarget).prop('checked')
            });
        },
        reset: function () {
            this.node = undefined;
            this.render();
        },
        close: function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NetboxInfoView;
});






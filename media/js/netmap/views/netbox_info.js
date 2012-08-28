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
                var out = this.template({ node: self.node});
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
            this.broker.trigger('map:show_vlan', $(e.currentTarget).data().navVlan);
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






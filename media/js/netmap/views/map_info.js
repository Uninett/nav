define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/map_info.html',
    'views/netbox_info',
    'views/link_info'
], function ($, _, Backbone, Handlebars, NetmapHelpers, mapInfoTemplate, NetboxInfoView, LinkInfoView) {

    var MapInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {

        },
        initialize: function () {
            this.template = Handlebars.compile(mapInfoTemplate);
            Handlebars.registerHelper('toLowerCase', function (value) {
                return (value && typeof value === 'string') ? value.toLowerCase() : '';
            });

            this.render();
            //this.netboxInfoView = new NetboxInfoView({el: $(this.el).find("#nodeinfo")});

            /*this.model.bind("change", this.render, this);
             this.model.bind("destroy", this.close, this);*/

        },
        swap_to_link: function (link) {
            if (this.netboxInfoView !== undefined) {
                this.netboxInfoView.close();
            }
            if (this.linkInfoView === undefined) {
                this.linkInfoView = new LinkInfoView({el: $("#linkinfo")});
            }
            this.linkInfoView.link = link;
            this.linkInfoView.render();
        },
        swap_to_netbox: function (netbox) {
            if (this.linkInfoView !== undefined) {
                this.linkInfoView.close();
            }
            if (this.netboxInfoView === undefined) {
                this.netboxInfoView = new NetboxInfoView({el: $("#nodeinfo")});
            }
            this.netboxInfoView.node = netbox;
            this.netboxInfoView.render();
        },
        render: function () {
            var self = this;
            var out = this.template();
            this.$el.html(out);
            return this;
        },
        close: function () {
            this.linkInfoView.close();
            this.netboxInfoView.close();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return MapInfoView;
});






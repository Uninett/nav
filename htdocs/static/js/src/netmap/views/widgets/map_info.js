define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/widgets/map_info.html',
    'netmap/views/widgets/netbox_info',
    'netmap/views/widgets/link_info',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, mapInfoTemplate, NetboxInfoView, LinkInfoView) {

    var MapInfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            "netmap:selectNetbox": "setSelectedNetbox",
            "netmap:selectLink": "setSelectedLink",
            "netmap:nodes:setFixedDone": "render"
        },
        events: {
        },
        initialize: function () {
            this.linkInfoView = null;
            this.netboxInfoView = null;

            this.broker.register(this);
            this.template = Handlebars.compile(mapInfoTemplate);

            this.render();

        },
        setSelectedNetbox: function (data) {
            if (this.linkInfoView.hasLink()) {
                this.linkInfoView.reset();
            }
            this.netboxInfoView.setNode(data.netbox, data.selectedVlan);
        },
        setSelectedLink: function (data) {
            if (this.netboxInfoView.hasNode()) {
                this.netboxInfoView.reset();
            }

            this.linkInfoView.setLink(data.link, data.selectedVlan);
        },
        render: function () {
            var self = this;
            var out = this.template();
            this.$el.html(out);
            this.linkInfoView = this.attachSubView(this.linkInfoView, LinkInfoView, '#linkinfo');
            this.netboxInfoView = this.attachSubView(this.netboxInfoView,
                NetboxInfoView,
                {
                    el: '#nodeinfo',
                    isWidgetVisible: true
                }
            );
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






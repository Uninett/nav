define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/searchbox.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, netmapTemplate) {

    var SearchboxView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
            "click #searchbox_search": "searchMap",
            "click #center_graph": "centerGraph"
        },
        initialize: function () {

            this.template = Handlebars.compile(netmapTemplate);

            //this.searchbox = this.options.node;
            /*this.model.bind("change", this.render, this);
             this.model.bind("destroy", this.close, this);*/

        },
        searchMap: function (e) {
            e.preventDefault();
            this.broker.trigger('map:search', $("input#searchbox_query", this.$el).val());
        },
        centerGraph: function (e) {
            e.preventDefault();
            this.broker.trigger('map:centerGraph');
        },
        render: function () {
            var self = this;
            var out = this.template({ node: self.node});
            this.$el.html(out);
            return this;
        },
        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return SearchboxView;
});






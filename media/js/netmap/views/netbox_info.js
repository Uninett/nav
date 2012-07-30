define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/netbox_info.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, netmapTemplate) {

    var NetboxInfoView = Backbone.View.extend({
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
            var out = this.template({ node: self.node});
            this.$el.html(out);
            return this;
        },
        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NetboxInfoView;
});






define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/info.html',
    'netmap/views/list_maps',
    'netmap/views/map_info',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, Template, ListMapPropertiesView, MapInfoView) {

    var InfoView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest'
        },
        events: {
            'click #toggle_view':      'toggleView'
        },
        initialize: function () {
            this.listMapPropertiesView = null;
            this.mapInfoView = null;

            this.isContentVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(Template);

            this.isLoading = !!(this.options.isLoading);

        },
        setLoading: function (state) {
            this.isLoading = state;
            this.render();
        },
        eventLoadingDone: function () {
            this.isLoading = false;
            this.render();
        },
        render: function () {
            var self = this;
            var context = {
                isVisible: this.isContentVisible,
                isLoading: this.isLoading
            };

            if ($("#netmap_link_to_admin").length !== 0) {
                context.link_to_admin = $("#netmap_link_to_admin").html().trim();
            } else {
                context.link_to_admin = false;
            }

            var out = this.template(context);
            this.$el.html(out);

            this.listMapPropertiesView = this.attachSubView(this.listMapPropertiesView, ListMapPropertiesView, '#list_mapproperties_view');
            this.mapInfoView = this.attachSubView(this.mapInfoView, MapInfoView, '#map_info_view');

            return this;
        },
        headerFooterMinimizeRequest: function (options) {
            if (options && options.name === 'header' && (options.isShowing !== this.isContentVisible)) {
                this.toggleView();
            }
        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();

            this.broker.trigger('map:resize:animate', {marginRight: margin});
        },
        alignView: function () {
            var $helper = $(this.$el);
            var $helper_content = $(".inner_wrap", this.$el);

            var margin;

            if (!this.isContentVisible) {
                margin = 30;
                $("a#toggle_view", this.$el).html("&lt;&lt;");

                $helper_content.fadeOut('fast');
                $helper.animate({'width': "{0}px".format(12) }, 400);
            } else {
                margin = 210;

                $("a#toggle_view", this.$el).html("&gt;&gt;");

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin - 40) }, 400);
            }
            return margin;
            //$("#netmap_main_view").animate({'margin-right': "{0}px".format(margin)}, 400);
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return InfoView;
});
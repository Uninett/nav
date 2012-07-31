define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'models/map',
    'models/graph',
    'views/modal/save_new_map',
    'text!templates/list_maps.html'

], function ($, _, Backbone, Handlebars, NetmapExtras, MapModel, GraphModel, SaveDialogView, netmapTemplate) {

    var ListNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "choose_netview",

        events: {
                "click #save_view": "show_save_view",
                "click #save_new_view": "new_show_save_view",
                "change #dropdown_view_id": "changed_view",
                'click #toggle_view' : 'toggleView'
        },
        initialize: function () {
            this.isContentVisible = true;

            this.template = Handlebars.compile(netmapTemplate);


            this.collection.bind("reset", this.render, this);
            this.collection.bind("change", this.render, this);
            this.collection.bind("destroy", this.close, this);
            this.options.context_selected_map.map.bind("change", this.render, this);
        },
        showSaveModal:     function (netmapModel) {
            var self = this;
            if (self.modal_save_view !== undefined) {
                self.modal_save_view.close();
            }
            if (this.options.context_selected_map === undefined) {
                debugger;
            }

            self.modal_save_view = new SaveDialogView({model: self.options.context_selected_map.map, 'graph': self.options.context_selected_map.graph});



            self.modal_save_view.render();
        },
        new_show_save_view: function () {
            var self = this;
            console.log("YUPPP");
            self.options.context_selected_map.map = new MapModel();
            self.options.context_selected_map.map.bind("change", this.render, this);

            this.showSaveModal(self.context_selected_map);
        },
        show_save_view: function (e) {
            e.preventDefault();
            var self = this;
            var selected_id = this.$("#dropdown_view_id :selected").val();
            this.showSaveModal(self.context_selected_map);
        },
        changed_view: function () {
            var self = this;


            self.selected_id = parseInt(this.$("#dropdown_view_id :selected").val().trim());
            if (isNaN(self.selected_id)) {
                // assume new

                self.options.context_selected_map.map = new MapModel();
                self.options.context_selected_map.map.bind("change", this.render, this);
            } else {
                self.options.context_selected_map.map = self.collection.get(self.selected_id);
            }


            if (!self.options.context_selected_map.map.isNew() && self.is_selected_view_really_changed(self.selected_id, self.options.context_selected_map.map)) {
                Backbone.history.navigate("netmap/{0}".format(self.selected_id));
                self.loadMapFromContextId(self.selected_id);
            }
        },
        loadMapFromContextId: function (map_id) {
            var self = this;
            self.options.context_selected_map.map.unbind("change");
            self.options.context_selected_map.map = self.collection.get(map_id);
            //self.options.context_selected_map.map.bind("change", this.render, this);
            self.options.context_selected_map.graph = new GraphModel({id: map_id});
            self.options.context_selected_map.graph.fetch({
                success: function (model) {
                    self.options.context_selected_map.graph = model;
                    //self.render();
                    self.options.context_selected_map.trigger('reattach', self.options.context_selected_map);
                }
            });
            /*self.options.context_selected_map.map.fetch({
                success: function (model) {
                    debugger;
                    self.options.context_selected_map.map = model;
                    self.options.context_selected_map.map.bind("change", this.render, this);
                    //self.render();
                }
            })*/
        },
        toggleView: function (e) {
            //debugger;
            var $helper = $(this.$el.parent().parent());
            var $helper_content = $(".inner_wrap", this.$el);

            var margin;

            if (!this.isContentVisible) {
                margin = 210;

                $("a#toggle_view", this.$el).html("&gt;&gt;");

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin - 40) }, 400);


            } else {
                margin = 30;
                $("a#toggle_view", this.$el).html("&lt;&lt;");

                $helper_content.fadeOut('fast');
                $helper.animate({'width': "{0}px".format(12) }, 400);

            }

            $("#netmap_main_view").animate({'margin-right': "{0}px".format(margin)}, 400);

            this.isContentVisible = !this.isContentVisible;
        },
        render: function () {
            var context = {};
            context.maps = this.collection.toJSON();

            console.log(this.options.context_selected_map.map.attributes.title);
            context.context_selected_map = this.options.context_selected_map.map.toJSON();

            var out = this.template(context);

            this.$el.html(out);
            return this;
        },
        close:function () {
            console.log("CLOSING LIST NETMAP VIEW");
            $(this.el).unbind();
            $(this.el).remove();
        },

        // private methods
        is_selected_view_really_changed: function (selected_id, selected_netmap)  {
            return selected_netmap !== undefined && selected_id !== undefined && selected_id != selected_netmap.attributes.id;
        }
    });
    return ListNetmapView;
});






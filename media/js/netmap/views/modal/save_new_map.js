define([
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'netmapextras',
    'text!templates/modal/save_new_map.html',
    'jqueryui/dialog'
], function ($, _, Backbone, Handlebars, NetmapHelpers, template) {

    var modalSaveNew = Backbone.View.extend({
        events: {
            "click #save_new_view": "save_view"
        },
        initialize: function () {
            this.template_post = Handlebars.compile(template);

            // Parent list view collection of models
            this.model_collection = this.options.model_collection;
            this.graph = this.options.graph;

            this.el = $(this.template_post({'model': this.model.toJSON(), 'is_new': this.model.isNew()})).dialog({autoOpen: false});
            this.$el = $(this.el);

            if (this.graph === undefined) {  debugger }

            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);

        },
        render: function () {
            this.el.dialog('open');
            return this;
        },
        get_fixed_nodes: function () {
            var fixed_nodes = [];

            for (var i = 0; i < this.graph.attributes.nodes.length; i++) {
                var node = this.graph.attributes.nodes[i];
                if (node.fixed == true && node.data.category !== 'ELINK') {
                    fixed_nodes.push(node);
                }
            }
            return fixed_nodes;

                /*data['fixed_nodes'] = JSON.stringify(fixed_nodes);
                data['link_types'] = "2";
                data['zoom'] = [trans, scale].join(";");*/
        },
        save_view: function () {
            var self = this;

            //self.$('#choose_netview form').attr('action', this.model.url)

            // make a copy
            //var copy = $.extend(true, {}, this.model);
            this.model.set({
                title: self.$('#new_view_title').val().trim(),
                description: self.$('#new_view_description').val().trim(),
                is_public: (self.$('#new_view_is_public').attr('checked') ? true : false),
                nodes: self.get_fixed_nodes(),
                //zoom: self.graph.zoom,
                topology: self.model.attributes.topology,
                categories: self.model.attributes.categories,
                zoom: self.model.attributes.zoom,
                display_orphans: !self.model.attributes.display_orphans
            });
            console.log("====" + "savedata");
            console.log($.extend(true, {}, this.model.attributes));
            console.log("====/" + "savedata");
            this.model.save(this.model.attributes, {
                wait: true,
                error: function () { alert("Error while saving view, try again"); },
                success: function (model, response) {


                    model.set({'viewid': response});
                    //self.collection.add(model);


                    Backbone.View.goTo("netmap/{0}".format(response));
                    //Backbone.navigate("netmap/{0}".format(response));
                    //window.location = "#/netmap/{0}".format(response);
                }
            });
            //this.model.trigger('change');
            this.close();
        },
        close: function () {
            console.log("SAVE NEW VIEW CLOSED");

            $('#modal_new_view').dialog('destroy').remove();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return modalSaveNew;
});






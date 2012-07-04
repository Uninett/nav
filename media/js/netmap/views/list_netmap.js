define([
    'jQuery',
    'Underscore',
    'Backbone',
    'Handlebars',
    'Netmap',
    'views/modal/save_new_view',
    'text!templates/list_netmap.html'

], function ($, _, Backbone, Handlebars, NetmapHelpers, SaveDialogView, netmapTemplate) {

    var ListNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "choose_netview",

        events: {
                "click #save_view": "save_view",
                "change #dropdown_view_id": "changed_view"
        },
        initialize: function () {

            this.template = Handlebars.compile(netmapTemplate);

            this.selected_netmap = this.options.options.selected_netmap;
            console.log("====" + "selected map constructor");
            console.log(this.selected_netmap);
            console.log("====/" + "selected map constructor");

            //this.collection = postsCollection;
            this.collection.bind("change", this.render, this);
            this.collection.bind("destroy", this.close, this);
            /*this.collection = postsCollection.add({ id:1, title: "Twitter"});
             this.collection = postsCollection.add({ id:2, title: "Facebook"});
             this.collection = postsCollection.add({ id:3, title: "Myspace", score: 20});*/
            /*this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);*/

        },
        exampleBind: function (model) {
            //console.log(model);
        },
        save_view: function () {
            "use strict";
            var self = this;
            var selected_id = this.$("#dropdown_view_id :selected").val();
            if (self.modal_save_view != undefined) {
                self.modal_save_view.close();
            }

            self.modal_save_view = new SaveDialogView({model: this.collection.get(selected_id)});
            self.modal_save_view.render();


            //$('#netmap_infopanel')

        },
        changed_view: function () {
            "use strict";
            var self = this;
            self.selected_id = this.$("#dropdown_view_id :selected").val();
            self.selected_netmap = self.collection.get(self.selected_id);
            if (parseInt(self.selected_id) != -1) {
                window.location = "#/netmap/{0}".format(self.selected_id);
            }
        },



        render: function () {
            var netmaps_json = this.collection.toJSON();
            var compare = this.selected_netmap.toJSON()[0];
            if (compare !== undefined && compare.viewid != -1) {
                for (var i = 0; i < netmaps_json.length; i++) {
                    if (compare.viewid === netmaps_json[i].viewid) {
                        netmaps_json.splice(i, 1);
                        break;
                    }
                }
            }
            console.log("====" + "netmaps");
            console.log(netmaps_json);
            console.log("====/" + "netmaps");

            var out = this.template({ netmaps: netmaps_json, selected_netmap: this.selected_netmap.toJSON()[0] });
            this.$el.html(out);
            return this;
        },
        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return ListNetmapView;
});






define([
    'jQuery',
    'Underscore',
    'Backbone',
    'Handlebars',
    'Netmap',
    // Pull in the Collection module from above
    'text!templates/modal/save_new_view.html'
], function ($, _, Backbone, Handlebars, NetmapHelpers, template) {

    var modalSaveNew = Backbone.View.extend({
        events: {
            "click #save_new_view": "save_view"
        },
        initialize: function () {
            this.template_post = Handlebars.compile(template);

            this.$el = $(this.template_post(this.model.toJSON())).dialog({autoOpen: false});

        },
        render: function () {
            this.$el.dialog('open');
            return this;
        },
        save_view: function () {
            "use strict";
            console.log("====" + "saving");
            console.log(this.model);
            console.log("====/" + "saving");


            this.close();
        },
        close: function () {
            $('#modal_new_view').dialog('destroy').remove();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return modalSaveNew;
});






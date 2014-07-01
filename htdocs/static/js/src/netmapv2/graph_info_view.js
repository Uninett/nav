define([
    'libs-amd/text!resources/netmap/node_info_modal.html',
    'libs/handlebars',
    'libs/backbone',
    'libs/jquery-ui-1.8.21.custom.min'
], function (Template) {

    Handlebars.registerHelper('lowercase', function (type) {
        if (typeof type === 'string' || type instanceof String) {
            return type.toLowerCase();
        } else {
            return type;
        }
    });

    return Backbone.View.extend({



        initialize: function () {

            this.template = Handlebars.compile(Template);
            this.model.img = window.netmapData.staticURL +
                this.model.category.toLowerCase() + '.png';
            console.log(this.model);
            this.el = $(this.template(this.model)).dialog({
                autoOpen: true,
                resizable: false,
                width: 'auto',
                title: this.model.sysname
            });
        }
    });
});
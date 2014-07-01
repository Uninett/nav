define([
    'libs-amd/text!resources/netmap/node_info_modal.html',
    'libs-amd/text!resources/netmap/link_info_modal.html',
    'libs/handlebars',
    'libs/backbone',
    'libs/jquery-ui-1.8.21.custom.min'
], function (NodeTemplate, LinkTemplate) {

    Handlebars.registerHelper('lowercase', function (type) {
        if (typeof type === 'string' || type instanceof String) {
            return type.toLowerCase();
        } else {
            return type;
        }
    });

    var nodeTemplate = Handlebars.compile(NodeTemplate);
    var linkTemplate = Handlebars.compile(LinkTemplate);

    return Backbone.View.extend({

        initialize: function () {

            var title;

            if (this.model.sysname) { // E.g. model is a node
                this.template = nodeTemplate;
                this.model.img = window.netmapData.staticURL +
                    this.model.category.toLowerCase() + '.png';
                title = this.model.sysname;
            } else {
                this.template = linkTemplate;
                this.model.sourceImg = window.netmapData.staticURL +
                    this.model.source.category.toLowerCase() + '.png';
                this.model.targetImg = window.netmapData.staticURL +
                    this.model.target.category.toLowerCase() + '.png';
                title = 'Link';
            }

            this.el = $(this.template(this.model)).dialog({
                position: {
                    my: 'left top',
                    at: 'left top',
                    of: this.options.parent
                },
                autoOpen: true,
                resizable: false,
                width: 'auto',
                title: title
            });
        }
    });
});
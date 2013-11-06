define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/modal/save_new_map.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/jquery-ui-1.8.21.custom.min'
], function (NetmapHelpers, template) {

    var modalSaveNew = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph": "setGraph"
        },
        events: {
            "click #modal_save_view_button": "save_view",
            "submit": function () { return false; }
        },
        initialize: function () {
            this.broker.register(this);
            this.template_post = Handlebars.compile(template);
            if (!this.options.graph || !this.options.model) {
                alert("Missing graph data or view properties, cannot save!");
                this.close();
            } else {
                if (!this.options.isNew && !this.model.get('viewid')) {
                    this.options.isNew = true;
                    this.options.fromUnsavedView = this.model;
                }
                this.el = $(this.template_post({
                    'model': this.model.toJSON(),
                    'isNew': this.options.isNew,
                    imagePath: NAV.imagePath
                })).dialog({
                        autoOpen: false,
                        zIndex: 500
                    });
                this.$el = $(this.el);

                this.model.bind("change", this.render, this);
                this.model.bind("destroy", this.close, this);
            }
        },
        setGraph: function (graphModel) {
            this.options.graph = graphModel;
        },
        render: function () {
            this.el.dialog('open');
            return this;
        },
        get_fixed_nodes: function () {
            var fixed_nodes = _.filter(this.options.graph.get('nodes'), function (node) {
                return node.fixed === true &&
                    node.get('category') &&
                    node.get('category').toUpperCase() !== 'ELINK';
            });
            return fixed_nodes;
        },
        save_view: function () {
            var self = this;
            if (this.options.isNew) {
                this.model = this.model.clone();
                this.model.unset('viewid');
            }
            //this.model.
            this.model.set({
                title: self.$('#new_view_title').val().trim(),
                description: self.$('#new_view_description').val().trim(),
                is_public: self.$('#new_view_is_public').prop('checked'),
                nodes: self.get_fixed_nodes(),
                topology: self.model.get('topology'),
                categories: self.model.get('categories'),
                zoom: self.model.get('zoom'),
                display_orphans: self.model.get('displayOrphans')
            });

            this.model.save(this.model.attributes, {
                wait: true,
                error: function () {
                    alert("Error while saving view, try again");
                    self.model.set({'viewid': self.options.transactionAbortId}, {silent: true});
                },
                success: function (model, response) {
                    model.set({'viewid': response});
                    Backbone.View.navigate("view/{0}".format(response));

                    if (self.options.fromUnsavedView) {
                        self.broker.trigger('netmap:save:removeUnsavedView', self.options.fromUnsavedView);
                    }
                    if (self.options.isNew) {
                        self.broker.trigger('netmap:save:newMapProperties', model);
                    }
                    // Hack for: need a clean way to trigger render() in
                    // parent view (list_maps) to render dropdown again.
                    // Since model doesn't trigger a change we'll use
                    // backbone.eventbroker to just trigger a re-render in
                    // list_maps...
                    self.broker.trigger('netmap:setMapProperties:done', model);
                }
            });
            this.close();
        },
        close: function () {
            this.broker.unregister(this);
            $('#modal_new_view').dialog('destroy').remove();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return modalSaveNew;
});

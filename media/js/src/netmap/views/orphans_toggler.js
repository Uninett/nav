define([
    'netmap/resource',
    'libs-amd/text!netmap/templates/orphans_toggler.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Resource, Template) {
    var OrphanView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="filter_orphans"]': 'setOrphansFilter'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);
            // todo: fetch collection from api.
            if (!this.model) {
                this.model = Resource.getMapProperties();
            }

            this.model.bind("change:displayOrphans", this.render, this);
            return this;
        },

        render: function () {
            this.$el.html(
                this.template({model: this.model.toJSON()})
            );

            return this;
        },
        setOrphansFilter: function (e) {
            this.model.set({'displayOrphans': !($(e.currentTarget).prop('checked'))});
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return OrphanView;
});

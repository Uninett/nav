define([
    'netmap/models/orphan',
    'libs-amd/text!netmap/templates/orphans_toggler.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Model, Template) {
    var OrphanView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="filter_orphans"]': 'setOrphansFilter'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);
            // todo: fetch collection from api.
            if (!this.model) {
                this.model = new Model();

            }

            this.model.bind("change", this.broadcastOrphanFilter, this);
            this.model.bind("change", this.render, this);

            return this;
        },

        render: function () {
            this.$el.html(
                this.template({model: this.model.toJSON()})
            );

            return this;
        },
        broadcastOrphanFilter: function () {
            this.broker.trigger("netmap:changeOrphansFilters", this.model);
        },
        setOrphansFilter: function (e) {
            this.model.set({'is_filtering_orphans': $(e.currentTarget).prop('checked')});
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return OrphanView;
});

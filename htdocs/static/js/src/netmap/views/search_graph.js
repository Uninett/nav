define([
    'libs/jquery',
    'libs/backbone',
    'libs/backbone-eventbroker'], function () {

    var GraphNavigationView = Backbone.View.extend({

        el: '#graph-navigation',

        interests: {},
        events: {
            'click #graph-search-submit': 'searchGraph',
            'click #view-options-toggle': 'toggleViewOptions',
            'change #graph-layer-select': 'selectLayer',
            'change #graph-view-select': 'selectView'
        },

        initialize: function () {
            console.log('Initializing GraphNavigationView');

            this.input_element = $('input#graph-search-query', this.$el);
            this.layer_select_element = $('select#graph-layer-select', this.$el);
            this.view_select_element = $('select#graph-view-select', this.$el);

            Backbone.EventBroker.register(this);
        },

        searchGraph: function (e) {
            e.preventDefault();
            console.log('Searching for ' + this.input_element.val());

            Backbone.EventBroker.trigger('netmap:search', this.input_element.val());
        },

        selectLayer: function (e) {
            e.preventDefault();

            var layer = parseInt(this.layer_select_element.val());
            console.log('Selected layer changed to ' + layer);

            Backbone.EventBroker.trigger('netmap:changeTopology', layer);
        },

        selectView: function (e) {
            e.preventDefault();

            var view_id = this.view_select_element.find(':selected').data('view_id');

            console.log('Selected view changed to ' + view_id);

            Backbone.View.navigate('view/' + view_id);
            Backbone.EventBroker.trigger('netmap:selectVlan', null);
        },

        toggleViewOptions: function (e) {
            e.preventDefault();

            var elem = $('#view-options-toggle i', this.$el);
            var panel = $('#graph-view-panel');
            if (elem.hasClass('fa-caret-down')) {
                elem.removeClass('fa-caret-down');
                elem.addClass('fa-caret-up');
            } else {
                elem.removeClass('fa-caret-up');
                elem.addClass('fa-caret-down');
            }
            panel.toggle(400);

        }
    });

    return GraphNavigationView;
});

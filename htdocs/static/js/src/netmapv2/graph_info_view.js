define([
    'netmap/collections',
    'libs-amd/text!resources/netmap/node_info_modal.html',
    'libs-amd/text!resources/netmap/link_info_modal.html',
    'libs-amd/text!resources/netmap/vlan_info_modal.html',
    'libs/handlebars',
    'libs/backbone',
    'libs/jquery-ui-1.8.21.custom.min'
], function (Collections, NodeTemplate, LinkTemplate, VlanTemplate) {

    Handlebars.registerHelper('lowercase', function (type) {
        if (typeof type === 'string' || type instanceof String) {
            return type.toLowerCase();
        } else {
            return type;
        }
    });

    var nodeTemplate = Handlebars.compile(NodeTemplate);
    var linkTemplate = Handlebars.compile(LinkTemplate);
    var vlanTemplate = Handlebars.compile(VlanTemplate);

    return Backbone.View.extend({

        el: '#graph-info-view',

        events: {
            'click #graph-info-vlan-list .vlan': 'selectVlan'
        },

        interests: {},

        initialize: function () {

            this.$el.dialog({
                position: {
                    my: 'left top',
                    at: 'left top',
                    of: this.options.parent
                },
                autoOpen: false,
                resizable: false,
                width: 'auto'
            });

            Backbone.EventBroker.register(this);
        },

        render: function () {

            this.$el.html(this.template(this.model));

            if (!this.$el.dialog('isOpen')) {
                this.$el.dialog('open');
            }
        },

        setModel: function (model) { // TODO: Refactor

            var title;
            model = _.extend({}, model); // Make a copy :)

            if (model.sysname) { // Model is a node

                this.template = nodeTemplate;
                model.img = window.netmapData.staticURL +
                    model.category.toLowerCase() + '.png';

                model.vlans = _.map(model.vlans, function (vlanId) {
                    return this.vlans.get(vlanId).attributes;
                }, this);

                title = model.sysname;

            } else if (_.isArray(model.edges)) { // Model is a layer2 link

                this.template = linkTemplate;
                model.sourceImg = window.netmapData.staticURL +
                    model.source.category.toLowerCase() + '.png';
                model.targetImg = window.netmapData.staticURL +
                    model.target.category.toLowerCase() + '.png';

                var sourceVlans = model.source.vlans;
                var targetVlans = model.target.vlans;
                if (!sourceVlans) {
                    sourceVlans = [];
                }
                if (!targetVlans) {
                    targetVlans = [];
                }
                model.vlans = _.map(
                    _.intersection(sourceVlans, targetVlans),
                    function (vlanId) {
                        return this.vlans.get(vlanId).attributes;
                }, this);

                title = 'Layer 2 link';

            } else { // Model is a layer2 link

                this.template = vlanTemplate;
                model.sourceImg = window.netmapData.staticURL +
                    model.source.category.toLowerCase() + '.png';
                model.targetImg = window.netmapData.staticURL +
                    model.target.category.toLowerCase() + '.png';

                title = 'Layer 3 link';

                // Attach vlan objects to each edge
                model.edges = _.map(model.edges, function (edges, vlanId) {

                    var vlan = this.vlans.get(vlanId);

                    edges.vlan = vlan.attributes;

                    return edges;
                }, this);
            }

            this.model = model;

            this.$el.dialog('option', 'title', title);
        },

        selectVlan: function (e) { // TODO: Selected vlan across clicks!

            var target = $(e.currentTarget);
            var vlanId = target.data('nav-vlan');

            this.$('#graph-info-vlan-list .selected-vlan').removeClass('selected-vlan');
            target.addClass('selected-vlan');

            Backbone.EventBroker.trigger('netmap:selectedVlanChanged', vlanId);
        },

        setVlans: function (vlans) {
            this.vlans = vlans;
        }

    });
});
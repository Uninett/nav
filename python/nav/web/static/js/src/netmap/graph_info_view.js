define([
    'netmap/collections',
    'plugins/netmap-extras',
    'libs-amd/text!resources/netmap/node_info.html',
    'libs-amd/text!resources/netmap/layer2_link_info.html',
    'libs-amd/text!resources/netmap/layer3_link_info.html',
    'libs/handlebars',
    'libs/backbone',
    'jquery-ui'
], function (Collections, NetmapExtras ,NodeTemplate, LinkTemplate, VlanTemplate, Handlebars) {

    /**
     * View for rendering a modal with detailed node-/link-info
     */

    // Template helper for formatting traffic data
    Handlebars.registerHelper('traffic_data', function (node) {
        if (node) {
            var traffic = NetmapExtras.convert_bits_to_si(node.in_bps);
            var percent = node.percent_by_speed ? '(' + node.percent_by_speed + '%' + ')' : '';
            return traffic + ' ' + percent;
        } else {
            return node;
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
                width: 'auto',
                appendTo: this.options.parent
            });

            this.selectedVlan = -1;
            Backbone.EventBroker.register(this);
        },

        render: function () {

            this.$el.html(this.template(this.model));

            if (!this.$el.dialog('isOpen')) {
                this.$el.dialog('open');
            }
        },

        /**
         * Changes the model to be represented in this view.
         */
        setModel: function (_model) {

            var title;
            var model = _.extend({}, _model); // Make a copy

            if (model.sysname) { // Model is a node

                this.template = nodeTemplate;
                this.attachNodeMeta(model);
                title = model.sysname;

            } else if (_.isArray(model.edges)) { // Model is a layer2 link

                this.template = linkTemplate;
                this.attachLayer2LinkMeta(model);
                title = 'Layer 2 link';

            } else { // Model is a layer2 link

                this.template = vlanTemplate;
                this.attachLayer3LinkMeta(model);
                title = 'Layer 3 link';
            }

            this.model = model;

            this.$el.dialog('option', 'title', title);
        },

        /**
         * Extend the model with metadata for a node detail view
         */
        attachNodeMeta: function (model) {

            model.img = window.netmapData.staticURL +
                model.category.toLowerCase() + '.png';

            model.vlans = _.map(model.vlans, function (vlanId) {
                var vlan = this.vlans.get(vlanId).attributes;
                vlan.isSelected = vlanId === this.selectedVlan;
                return vlan;
            }, this);

            return model;
        },

        /**
         * Extend the model with metadata for a layer2 link detail view
         */
        attachLayer2LinkMeta: function (model) {

            model.sourceImg = window.netmapData.staticURL +
                    model.source.category.toLowerCase() + '.png';
            model.targetImg = window.netmapData.staticURL +
                model.target.category.toLowerCase() + '.png';

            model.vlans = _.map(_.uniq(model.vlans), function (vlanId) {
                var vlan = this.vlans.get(vlanId).attributes;
                vlan.isSelected = vlanId === this.selectedVlan;
                return vlan;
            }, this).sort(function (a, b) { return a.vlan - b.vlan; });

            _.each(model.edges, function (edge) {
                if (model.traffic === undefined) return;
                edge.traffic = _.find(model.traffic.edges, function (traffic) {
                    var sourceTraffic, targetTraffic;
                    if (edge.source.interface) {
                        sourceTraffic = edge.source.interface.ifname === traffic.source_ifname ||
                            edge.source.interface.ifname === traffic.target_ifname;
                    }
                    if (edge.target.interface) {
                        targetTraffic = edge.target.interface.ifname === traffic.target_ifname ||
                            edge.target.interface.ifname === traffic.source_ifname;
                    }
                    return sourceTraffic || targetTraffic;
                });
            });

            return model;
        },

        /**
         * Extend the model with metadata for a layer3 link detail view
         */
        attachLayer3LinkMeta: function (model) {

            model.sourceImg = window.netmapData.staticURL +
                    model.source.category.toLowerCase() + '.png';
            model.targetImg = window.netmapData.staticURL +
                model.target.category.toLowerCase() + '.png';

            model.edges = _.map(model.edges, function (edges, vlanId) {
                return  {
                    vlan: this.vlans.get(vlanId).attributes,
                    edges: edges
                };
            }, this);

            /*
             * Sometimes the backend will supply multiple linknets.
             * The cause is usually wrongful categorization, perhaps due
             * to improper configuration. There is no way to know which is
             * the correct linknet from this end, so we display them all
             * along with a warning message.
             */
            if (model.edges.length > 1) { // TODO: Better warning message
                model.warning = 'Found multiple linknets! This can mean ' +
                'improper categorization by NAV or improper configuration';
            }

            return model;
        },

        /** Triggers when a specific vlan is selected. Notifies the GraphView */
        selectVlan: function (e) {

            var target = $(e.currentTarget);
            var vlanId = target.data('nav-vlan');

            if (vlanId === this.selectedVlan) {
                this.selectedVlan = -1;
                target.removeClass('selected-vlan');
                Backbone.EventBroker.trigger('netmap:resetTransparency');
                return;
            }

            this.selectedVlan = vlanId;

            this.$('#graph-info-vlan-list .selected-vlan').removeClass('selected-vlan');
            target.addClass('selected-vlan');

            Backbone.EventBroker.trigger('netmap:selectedVlanChanged', vlanId);
        },

        /** Resets the view */
        reset: function () {
            this.selectedVlan = -1;
            this.$el.dialog('close');
        },

        /** Set the list of vlans in this network */
        setVlans: function (vlans) {
            this.vlans = vlans;
        }

    });
});

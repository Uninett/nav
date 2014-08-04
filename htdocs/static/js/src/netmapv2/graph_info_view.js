define([
    'netmap/collections',
    'libs-amd/text!resources/netmap/node_info.html',
    'libs-amd/text!resources/netmap/layer2_link_info.html',
    'libs-amd/text!resources/netmap/layer3_link_info.html',
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

            this.selectedVlan = -1;
            Backbone.EventBroker.register(this);
        },

        render: function () {

            this.$el.html(this.template(this.model));

            if (!this.$el.dialog('isOpen')) {
                this.$el.dialog('open');
            }
        },

        setModel: function (model) {

            var title;
            model = _.extend({}, model); // Make a copy :)

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


        attachNodeMeta: function (model) {

            model.img = window.netmapData.staticURL +
                model.category.toLowerCase() + '.png';

            model.vlans = _.map(model.vlans, function (vlanId) {
                return this.vlans.get(vlanId).attributes;
            }, this);

            return model;
        },


        attachLayer2LinkMeta: function (model) {

            model.sourceImg = window.netmapData.staticURL +
                    model.source.category.toLowerCase() + '.png';
            model.targetImg = window.netmapData.staticURL +
                model.target.category.toLowerCase() + '.png';

            model.vlans = _.map(_.uniq(model.vlans), function (vlanId) {
                var vlan = this.vlans.get(vlanId).attributes;
                vlan.isSelected = vlanId === this.selectedVlan;
                return vlan;
            }, this);

            _.each(model.edges, function (edge) {
                if (model.traffic === undefined) return;
                var edgeTraffic = _.find(model.traffic.edges, function (traffic) {
                    if (edge.source.interface && edge.target.interface) {
                        return edge.source.interface.ifname === traffic.source_ifname
                            && edge.target.interface.ifname === traffic.target_ifname;
                    } else {
                        return false;
                    }
                });
                edge.traffic = edgeTraffic;
            });

            return model;
        },


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
             * The cause is usally wrongful categorization, perhaps due
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


        selectVlan: function (e) { // TODO: Selected vlan across clicks!

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

        setVlans: function (vlans) {
            this.vlans = vlans;
        }

    });
});
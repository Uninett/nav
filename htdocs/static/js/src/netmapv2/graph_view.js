define([
    'netmap/graph',
    'plugins/d3force',
    'plugins/set_equality',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/d3.v2'
], function (Graph, D3ForceHelper, Set) {

    var GraphView = Backbone.View.extend({

        el: '#graph-view',

        interests: {
            'netmap:topologyLayerChanged': 'updateTopologyLayer',
            'netmap:netmapViewChanged': 'updateNetmapView',
            'netmap:filterCategoriesChanged': 'updateFilterCategories',
            'netmap:graphUpdated': 'update',
            'netmap:renderGraph': 'render'
            // TODO
        },

        initialize: function () {

            // This does not seem to be bound automatically
            // For some reason...
            this.$el = $(this.el);

            // TODO: How to define a good starting height
            this.w = this.$el.width();
            this.h = 800;

            // Init state
            this.force = d3.layout.force()
                .gravity(0.1)
                .charge(-2500)
                .linkDistance(250)
                .size([this.w, this.h])
                ;

            this.nodes = this.force.nodes();
            this.links = this.force.links();
            this.isLoadingForTheFirstTime = true;



            Backbone.EventBroker.register(this);

            this.initializeDOM();
            this.bindEvents();

            this.model = new Graph();
            this.model.fetch({success: function () {
                Backbone.EventBroker.trigger('netmap:graphDoneLoading');
            }, error: function () {
                alert('Error loading graph, please try to reload the page');
            }});
        },

        initializeDOM: function () {

            this.svg = d3.select(this.el)
                .append('svg')
                .attr('width', this.w)
                .attr('height', this.h)
                .attr('viewBox', '0 0 ' + this.w + ' ' + this.h)
                .attr('overflow', 'hidden')
                ;

            // Markers for link cardinality
            var bundleLinkMarkerStart = this.svg.append('marker')
                .attr('id', 'bundlelinkstart')
                .attr('markerWidth', 8)
                .attr('markerHeight', 12)
                .attr('refX', -80)
                .attr('refY', 0)
                .attr('viewBox', '-4 -6 8 12')
                .attr('markerUnits', 'userSpaceOnUse')
                .attr('orient', 'auto');
            bundleLinkMarkerStart.append('rect')
                .attr('x', -3)
                .attr('y', -5)
                .attr('width', 2)
                .attr('height', 10);
            bundleLinkMarkerStart.append('rect')
                .attr('x', 1)
                .attr('y', -5)
                .attr('width', 2)
                .attr('height', 10);
            var bundleLinkMarkerEnd = this.svg.append('marker')
                .attr('id', 'bundlelinkend')
                .attr('markerWidth', 8)
                .attr('markerHeight', 12)
                .attr('refX', 80)
                .attr('refY', 0)
                .attr('viewBox', '-4 -6 8 12')
                .attr('markerUnits', 'userSpaceOnUse')
                .attr('orient', 'auto');
            bundleLinkMarkerEnd.append('rect')
                .attr('x', -3)
                .attr('y', -5)
                .attr('width', 2)
                .attr('height', 10);
            bundleLinkMarkerEnd.append('rect')
                .attr('x', 1)
                .attr('y', -5)
                .attr('width', 2)
                .attr('height', 10);

            // Needed to control the layering of elements
            this.linkGroup = this.svg.append('g').attr('id', 'link-group');
            this.nodeGroup = this.svg.append('g').attr('id', 'node-group');

            this.link = d3.selectAll('.link').data([]);
            this.node = d3.selectAll('.node').data([]);

        },

        bindEvents: function() {

            var self = this;

            // Set up zoom
            var zoomListener = d3.behavior.zoom()
                .scaleExtent([0.2, 3])
                .on('zoom', function () {
                    console.log('graph view zoom');
                    var translate = 'translate(' + d3.event.translate + ')';
                    var scale = 'scale(' + d3.event.scale + ')';
                    self.svg.attr('transform', translate + scale);
                });
            //this.svg.call(zoomListener);

            // Set up resize on window resize
            $(window).resize(function () {
                console.log('graph view resize');
                self.w = self.$el.width();
                self.svg.attr('width', self.w);
            });

            // Set up tick event
            this.force.on('tick', function () {

                self.link.attr('x1', function (o) {
                    return o.source.x;
                }).attr('y1', function (o) {
                    return o.source.y;
                }).attr('x2', function (o) {
                    return o.target.x;
                }).attr('y2', function (o) {
                    return o.target.y;
                });

                self.node.attr('transform', function(o) {
                    return 'translate(' + o.px + "," + o.py + ')';
                });
            });
        },

        /**
         * TODO: More efficient
         * @param nodes
         * @param links
         */
        updateNodesAndLinks: function (nodes, links) {

            // Get selected categories
            var categories = _.pluck(_.filter(
                this.model.get('filter_categories'),
                function (category) {
                    return category.checked;
            }), 'name');

            this.force
                .links(filterLinksByCategories(links, categories))
                .nodes(filterNodesByCategories(nodes, categories));

            this.nodes = this.force.nodes();
            this.links = this.force.links();
        },

        update: function () { console.log('graph view update');

            // You wouldn't want this running while updating
            this.force.stop();

            var nodes = this.model.get('nodeCollection').getGraphObjects();
            var vlans = this.model.get('vlanCollection').getGraphObjects();
            var links = this.model.get('linkCollection').getGraphObjects();

            if (this.isLoadingForTheFirstTime) {
                this.isLoadingForTheFirstTime = false;
            }

            this.updateNodesAndLinks(nodes, links);
            this.render();

            this.force.start();
        },

        render: function () { console.log('graph view render');

            this.link = this.linkGroup.selectAll('.link')
                .data(this.links, function (link) {
                    return link.source.id + '-' + link.target.id;
                });

            this.link.enter()
                .append('line')
                .attr('class', function (o) {
                    return 'link ' + linkSpeedAsString(findLinkMaxSpeed(o));
                })
                .attr('stroke', function (o) {
                    // TODO: Load based
                    return '#CCCCCC';
                })
                .attr('marker-start', function (o) {
                    if (o.edges.length > 1) {
                        return 'url(#bundlelinkstart)';
                    }
                })
                .attr('marker-end', function (o) {
                    if (o.edges.length > 1) {
                        return 'url(#bundlelinkend)';
                    }
                })
                ;

            this.link.exit().remove();

            this.node = this.nodeGroup.selectAll('.node')
                .data(this.nodes, function (node) {
                    return node.id;
                });

            var nodeElement = this.node.enter()
                .append('g')
                .attr('class', 'node')
                .on('dblclick', this.dblclick)
                .call(this.force.drag)
                ;

            nodeElement.append('image')
                .attr('xlink:href', function (o) {
                    return '/static/images/netmap/' + o.category.toLowerCase() + '.png';
                })
                .attr('x', -16)
                .attr('y', -16)
                .attr('width', 32)
                .attr('height', 32)
                ;

            nodeElement.append('text')
                .attr('class', 'sysname')
                .attr('dy', '1.5em')
                .attr('text-anchor', 'middle')
                .text(function (o) {
                    return o.sysname;
                })
                ;

            this.node.exit().remove();
        },

        updateTopologyLayer: function (layer) { console.log('graph view update topology');

            this.model.set('layer', layer);
            this.model.fetch();
        },

        updateNetmapView: function (view) { console.log('graph view update view');

            this.model.set('viewId', view.id);
            this.model.set('layer', view.get('topology'));

            var selectedCategories = view.get('categories');
            _.each(this.model.get('filter_categories'), function (category) {
                if (_.indexOf(selectedCategories, category.name) >= 0) {
                    category.checked = true;
                } else {
                    category.checked = false;
                }
            });

            this.update();
        },

        updateFilterCategories: function (categoryId, checked) { console.log('graph view update filter');


        },

       /* dragstart: function (node) { console.log('graph view dragstart');
            this.force.stop();
            d3.select(this).classed('fixed', node.fixed = true);
        },

        dragend: function (node) { console.log('graph view dragend');

        },*/

        dblclick: function (node) { console.log('graph view dblclick');
            d3.select(this).classed('fixed', node.fixed = false);
        }

    });

    /* Helper functions */

    /**
     * Helper function for filtering a list of nodes by a list of categories.
     * @param nodes
     * @param categories
     */
    function filterNodesByCategories(nodes, categories) {

        return _.filter(nodes, function (node) {
           return _.contains(categories, node.category);
        });
    }

    /**
     * Helper function for filtering a list of links by a list of categories.
     * @param links
     * @param categories
     */
    function filterLinksByCategories(links, categories) {

        return _.filter(links, function (link) {
            return _.contains(categories, link.source.category) &&
                _.contains(categories, link.target.category);
        });
    }


    /**
     * Helper function to find the max speed of a link objects
     * multiple edges, regardless of the layer
     * @param link
     */
    function findLinkMaxSpeed(link) {

        /*
        This is a kind of 'hacky' approach to find out which layer
        the link belongs to. This is needed because the JSON format
        of the object will be different depending on the layer.
         */
        var speed;
        if (Object.prototype.toString.call(link.edges) === "[object Array]") {
            speed = _.max(_.pluck(link.edges, 'link_speed'));
        } else {
            speed = _.max(_.pluck(_.flatten(_.values(link.edges)), 'link_speed'));
        }
        return speed;
    }

    /**
     * Helper function for converting the given speed into
     * the appropriate range class.
     * @param speed
     * @returns {*}
     */
    function linkSpeedAsString(speed) {
        var speedClass;
        if (speed <= 100) {
            speedClass = 'speed0-100';
        }
        else if (speed > 100 && speed <= 512) {
            speedClass = 'speed100-512';
        }
        else if (speed > 512 && speed <= 2048) {
            speedClass = 'speed512-2048';
        }
        else if (speed > 2048 && speed <= 4096) {
            speedClass = 'speed2048-4096';
        }
        else if (speed > 4096) {
            speedClass = 'speed4096';
        }
        else {
            speedClass = 'speedunknown';
        }
        return speedClass;
    }

    return GraphView;
});
define([
    'netmap/graph',
    'netmap/models',
    'netmap/graph_info_view',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    //'libs/d3.v2'
    'libs/d3.min'
], function (Graph, Models, GraphInfoView) {

    var Transparent = 0.2;
    var TransitionDuration = 500;
    var UndefinedLoad = '211,211,211';

    var GraphView = Backbone.View.extend({

        el: '#graph-view',

        interests: {
            'netmap:topologyLayerChanged': 'updateTopologyLayer',
            'netmap:netmapViewChanged': 'updateNetmapView',
            'netmap:filterCategoriesChanged': 'updateCategories',
            'netmap:filterByRoomOrLocation': 'addFilterString',
            'netmap:removeFilter': 'removeFilterString',
            'netmap:selectedVlanChanged': 'updateSelectedVlan',
            'netmap:updateGraph': 'update',
            'netmap:refreshGraph': 'refresh',
            'netmap:searchGraph': 'search',
            'netmap:saveNodePositions': 'saveNodePositions',
            'netmap:resetTransparency': 'resetTransparency',
            'netmap:resetZoom': 'resetZoom',
            'netmap:unfixNodes': 'unfixNodes',
            'netmap:toggleForce': 'toggleForce'
        },

        initialize: function () {

            // TODO: How to define a good starting height
            this.w = this.$el.width();
            this.h = 1200;

            // Initial d3 graph state
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

            this.model = new Graph();
            this.netmapView = this.options.netmapView;

            this.graphInfoView = new GraphInfoView({parent: this.el});
            this.filterStrings = [];

            this.initializeDOM();
            this.bindEvents();
            this.initializeNetmapView();
            this.fetchGraphModel();
        },

        /**
         * Initializes the graph model from the initially selected
         * or default netmapview.
         */
        initializeNetmapView: function () {

            if (this.netmapView === null) { console.log('netmapView === null');
                this.netmapView = new Models.NetmapView();
            }

            this.model.set('viewId', this.netmapView.id);
            this.model.set('layer', this.netmapView.get('topology'));

            var zoomStr = this.netmapView.get('zoom').split(';');
            this.baseZoom = zoomStr;
            this.trans = zoomStr[0].split(',');
            this.scale = zoomStr[1];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);

            var selectedCategories = this.netmapView.get('categories');
            _.each(this.model.get('filter_categories'), function (category) {
                category.checked = _.indexOf(selectedCategories, category.name) >= 0;
            });
        },

        /**
         * Initialize the SVG DOM elements
         */
        initializeDOM: function () {

            this.svg = d3.select(this.el)
                .append('svg')
                .attr('width', this.w)
                .attr('height', this.h)
                .attr('viewBox', '0 0 ' + this.w + ' ' + this.h)
                .attr('pointer-events', 'all')
                .attr('overflow', 'hidden')
                ;

            this.boundingBox = this.svg.append('g')
                .attr('id', 'boundingbox');

            // Markers for link cardinality
            var bundleLinkMarkerStart = this.boundingBox.append('marker')
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
            var bundleLinkMarkerEnd = this.boundingBox.append('marker')
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
            this.linkGroup = this.boundingBox.append('g').attr('id', 'link-group');
            this.nodeGroup = this.boundingBox.append('g').attr('id', 'node-group');

            this.link = d3.selectAll('.link').data([]);
            this.node = d3.selectAll('.node').data([]);

        },

        /**
         * Bind d3 events
         */
        bindEvents: function() {

            var self = this;

            // Set up zoom listener
            this.zoom = d3.behavior.zoom();
            this.svg.call(this.zoom.on('zoom', function () {
               self.zoomCallback.call(self);
            }));

            // Set up node dragging listener
            this.drag = d3.behavior.drag()
                .on('dragstart', function (node) {
                    self.dragStart.call(this, node, self);
                })
                //.on('drag', this.dragMove)
                .on('drag', function (node) {
                    self.dragMove.call(this, node, self);
                })
                //.on('dragend', this.dragEnd)
                .on('dragend', function (node) {
                    self.dragEnd.call(this, node, self);
                })
                ;

            // Set up resize on window resize
            $(window).resize(function () {
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
         * Gets the nodes and links from the model and filters out
         * those that should not be displayed
         */
        updateNodesAndLinks: function () {

            // Get selected categories
            var categories = _.pluck(_.filter(
                this.model.get('filter_categories'),
                function (category) {
                    return category.checked;
            }), 'name');

            var nodes = this.model.get('nodeCollection').getGraphObjects();
            var links = this.model.get('linkCollection').getGraphObjects();

            nodes = filterNodesByCategories(nodes, categories);
            links = filterLinksByCategories(links, categories);
            if (this.filterStrings.length) {
                nodes = filterNodesByRoomsOrLocations(nodes, this.filterStrings);
                links = filterLinksByRoomsOrLocations(links, this.filterStrings);
            }

            this.graphInfoView.setVlans(this.model.get('vlanCollection'));

            if (!this.netmapView.get('display_orphans')) {
                nodes = removeOrphanNodes(nodes, links);
            }

            this.force.links(links).nodes(nodes);

            this.nodes = this.force.nodes();
            this.links = this.force.links();

            // Set fixed positions
            _.each(this.nodes, function (node) {
                if (node.position) {
                    node.px = node.position.x;
                    node.py = node.position.y;
                    node.fixed = true;
                } else {
                    node.fixed = false;
                }
            });
        },

        update: function () {

            // You wouldn't want this running while updating
            this.force.stop();

            if (this.isLoadingForTheFirstTime) {
                this.isLoadingForTheFirstTime = false;
            }

            this.updateNodesAndLinks();
            this.transformGraph();
            this.render();

            this.force.start();
        },

        render: function () {
            var self = this;

            this.link = this.linkGroup.selectAll('.link')
                .data(this.links, function (link) {
                    return link.source.id + '-' + link.target.id;
                })
                .style('opacity', 1);

            this.link.enter()
                .append('line')
                .on('click', function (link) {
                    self.clickLink.call(this, link, self);
                })
                .attr('class', function (o) {
                    return 'link ' + linkSpeedAsString(findLinkMaxSpeed(o));
                })
                .attr('stroke', function (o) {
                    return 'url(#linkload' + o.source.id + '-' + o.target.id + ')';
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
                .attr('opacity', 0)
                    .transition()
                    .duration(TransitionDuration)
                    .attr('opacity', 1)
                ;


            this.link.exit().transition()
                .duration(TransitionDuration)
                .style('opacity', 0)
                .remove()
                ;

            this.node = this.nodeGroup.selectAll('.node')
                .data(this.nodes, function (node) {
                    return node.id;
                })
                .style('opacity', 1);

            var nodeElement = this.node.enter()
                .append('g')
                .attr('class', 'node')
                .on('click', function (node) {
                    self.clickNode.call(this, node, self);
                })
                .call(this.drag)
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

            nodeElement.attr('opacity', 0)
                .transition()
                .duration(TransitionDuration)
                .style('opacity', 1)
                ;

            this.node.exit()
                .transition()
                .duration(TransitionDuration)
                .style('opacity', 0)
                .remove()
                ;

            // Blaasal elink link disappears without this, possibly others
            this.linkGroup.selectAll('.linkload').remove();

            var gradient = this.linkGroup.selectAll('.linkload')
                .data(this.links);
            gradient.enter().append('linearGradient')
                .attr('class', 'linkload')
                .attr('id', function (link) {
                    return 'linkload' + link.source.id + '-' + link.target.id;
                })
                .attr('x1', '0%')
                .attr('x2', '0%')
                .attr('y1', '0%')
                .attr('y2', '100%')
                ;
            //gradient.exit().remove();

            var stops = gradient.selectAll('stop')
                .data(getTrafficCSSforLink)
                ;
            stops.enter()
                .append('stop')
                .attr('offset', function (gradient) {
                    return gradient.percent + '%';
                })
                .attr('style', function (gradient) {
                    if (gradient.css) {
                        return 'stop-color:rgb(' + gradient.css + '); stop-opacity:1';
                    }
                    else {
                        return 'stop-color:rgb(0,0,0);stop-opacity:1';
                    }
                });

            stops.exit().remove();
        },

        refresh: function () {

            if (this.netmapView.refreshTrafficOnly) { console.log('refreshing traffic');
                this.model.loadTraffic();
            } else {
                this.fetchGraphModel();
            }
        },

        fetchGraphModel: function () {

            var self = this;

            this.graphInfoView.reset();

            this.model.fetch({
                success: function () {
                    self.update();
                    self.model.loadTraffic();
                },
                error: function () { // TODO: Use alert message instead
                    alert('Error loading graph, please try to reload the page');
                }
            });
        },

        updateTopologyLayer: function (layer) {

            this.model.set('layer', layer);
            this.fetchGraphModel();
        },

        updateNetmapView: function (view) {

            this.netmapView = view;

            this.model.set('viewId', this.netmapView.id);
            this.model.set('layer', this.netmapView.get('topology'));

            var zoomStr = this.netmapView.get('zoom').split(';');
            this.trans = zoomStr[0].split(',');
            this.scale = zoomStr[1];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);

            var selectedCategories = this.netmapView.get('categories');
            _.each(this.model.get('filter_categories'), function (category) {
                category.checked = _.indexOf(selectedCategories, category.name) >= 0;
            });

            this.fetchGraphModel();
        },

        updateCategories: function (categoryId, checked) {

            var categories = this.model.get('filter_categories');
            _.find(categories, function (category) {
                return category.name === categoryId;
            }).checked = checked;

            this.update();
        },

        addFilterString: function (filter) {

            this.filterStrings.push(filter);
            this.update();
        },

        removeFilterString: function (filter) {

            this.filterStrings = _.without(this.filterStrings, filter);
            this.update();
        },

        saveNodePositions: function () {

            var self = this;

            var dirtyNodes = _.map(
                _.filter(this.force.nodes(), function (node) {
                    return node.fixed && node.category && !node.is_elink_node;
                }),
                function (dirtyNode) {
                    return {
                        viewid: self.netmapView.id,
                        netbox: dirtyNode.id,
                        x: dirtyNode.x,
                        y: dirtyNode.y
                    };
                }
            );

            if (dirtyNodes.length) {

                var nodePositions = new Models.NodePositions().set({
                    'data': dirtyNodes,
                    'viewid': this.netmapView.id
                });

                nodePositions.save(nodePositions.get('data'), {
                    success: function () { console.log('nodepositions saved'); },
                    error: function (model, resp, opt) {
                        console.log(resp.responseText);
                    }
                });

            }
        },

        updateSelectedVlan: function (vlanId) {

            var nodesInVlan = _.filter(this.nodes, function (node) {
                return _.contains(node.vlans, vlanId);
            });

            var linksInVlan = _.filter(this.links, function (link) {
                return _.contains(link.vlans, vlanId);
            });

            this.nodeGroup.selectAll('.node').style('opacity', 1)
                .filter(function (node) {
                    return !_.contains(nodesInVlan, node);
                })
                .transition()
                .duration(TransitionDuration)
                .style('opacity', Transparent);

            this.linkGroup.selectAll('.link').style('opacity', 1)
                .filter(function (link) {
                    return !_.contains(linksInVlan, link);
                })
                .transition()
                .duration(TransitionDuration)
                .style('opacity', Transparent);
        },

        resetTransparency: function () {
            this.render();
        },

        resetZoom: function () {

            var zoomStr = this.baseZoom;
            this.trans = zoomStr[0].split(',');
            this.scale = zoomStr[1];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);
            this.transformGraphTransition();
        },

        unfixNodes: function () {

            _.each(this.nodes, function (node) {
                node.fixed = false;
            });
            this.render();
        },

        toggleForce: function (statusOn) {
            if (statusOn) {
                this.force.stop();
            } else {
                this.force.resume();
            }
        },

        /**
         * Applies the current translation and scale transformations
         * to the graph
         */
        transformGraph: function () {
            this.boundingBox.attr(
                'transform',
                'translate(' + this.trans +
                ') scale(' + this.scale + ')'
            );
        },

        transformGraphTransition: function () {
               this.boundingBox.transition()
                   .duration(TransitionDuration)
                   .attr(
                        'transform',
                        'translate(' + this.trans +
                        ') scale(' + this.scale + ')');
        },

        transformGraphFromBounds: function (bounds) {

            var widthRatio = this.scale * (this.w / ((bounds.width + 300) * this.scale));
            var heightRatio = this.scale * (this.h / ((bounds.height + 300) * this.scale));

            if (widthRatio < heightRatio) {
                this.scale = widthRatio;
            } else {
                this.scale = heightRatio;
            }

            this.trans = [(-(bounds.xCenter * this.scale) + (this.w / 2)), (-(bounds.yCenter * this.scale) + (this.h / 2))];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);
            this.transformGraphTransition();
        },

        search: function (query) {

            this.nodeGroup.selectAll('.node').style('opacity', 1);

            var matchingNodes = _.filter(this.nodes, function (node) {
                    return node.sysname.search(query) !== -1;
                }
            );

            if (!matchingNodes.length) {
                // TODO: Inform of no matches
                return;
            } else {
                var bounds = findBoundingBox(matchingNodes);
                this.transformGraphFromBounds(bounds);

                this.nodeGroup.selectAll('.node')
                    .filter(function (node) {
                        return !_.contains(matchingNodes, node);
                    })
                    .transition()
                    .duration(TransitionDuration)
                    .style('opacity', Transparent);

                this.linkGroup.selectAll('.link')
                    .transition()
                    .duration(TransitionDuration)
                    .style('opacity', Transparent);
            }
        },

        /* d3 callback functions  */

        dragStart: function (node, self) {
            d3.event.sourceEvent.stopPropagation();
            d3.select(this).insert('circle', 'image').attr('r', 20);
            self.force.stop();
        },

        dragMove: function(node, self) {
            node.px += d3.event.dx;
            node.py += d3.event.dy;
            node.fixed = true;

            self.force.resume();
        },

        dragEnd: function (node, self) {
            d3.select(this).select('circle').remove();
        },

        zoomCallback: function () {

            this.trans = d3.event.translate;
            this.scale = d3.event.scale;
            this.transformGraph();
            this.netmapView.set('zoom', this.trans.join(',') + ';' + this.scale);
        },

        clickNode: function (node, self) {
            if (d3.event.defaultPrevented) {
                return;
            }
            self.graphInfoView.setModel(node);
            self.graphInfoView.render();
        },

        clickLink: function (link, self) {
            self.graphInfoView.setModel(link);
            self.graphInfoView.render();
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
            return _.contains(categories, node.category.toUpperCase());
        });
    }

    /**
     * Helper function for filtering a list of nodes by a list of
     * room or locations id's.
     * @param nodes
     * @param filters
     */
    function filterNodesByRoomsOrLocations(nodes, filters) {

        var s = filters.join();
        return _.filter(nodes, function (node) {
            return s.search(node.roomid + '|' + node.locationid) !== -1;
        });
    }

    /**
     * Helper function for filtering a list of links by a list of categories.
     * @param links
     * @param categories
     */
    function filterLinksByCategories(links, categories) {

        return _.filter(links, function (link) {
            return _.contains(categories, link.source.category.toUpperCase()) &&
                _.contains(categories, link.target.category.toUpperCase());
        });
    }

    /**
     * Helper function for filtering a list of links by a list of
     * room or location id's.
     * @param links
     * @param filters
     */
    function filterLinksByRoomsOrLocations(links, filters) {

        var s = filters.join();
        return _.filter(links, function (link) {
            return s.search(link.source.roomid + '|' + link.source.locationid) !== -1 &&
                s.search(link.target.roomid + '|' + link.target.locationid) !== -1;
        });
    }

    /**
     * Helper function for removing any orphaned nodes from the nodes list
     * @param nodes
     * @param links
     * @returns {*}
     */
    function removeOrphanNodes(nodes, links) {

        return _.filter(nodes, function (node) {
            return _.some(links, function (link) {
                return node.id === link.source.id || node.id === link.target.id;
            });
        });
    }

    /**
     * Helper function for filtering out any links whose source or target
     * is not in the node list.
     * @param nodes
     * @param links
     * @returns {*}
     */
    function filterLinksByNodes(nodes, links) {

        return _.filter(links, function (link) {
           return _.contains(nodes, link.source) && _.contains(nodes, link.target);
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

    /**
     * Helper function for finding the smallest bounding box
     * of a list of nodes.
     * @param nodes
     */
    function findBoundingBox(nodes) {

        var topLeft = {x: Number.MAX_VALUE, y: Number.MAX_VALUE};
        var topRight = {x: -Number.MAX_VALUE, y: Number.MAX_VALUE};
        var botLeft = {x: Number.MAX_VALUE, y: -Number.MAX_VALUE};
        var botRight = {x: -Number.MAX_VALUE, y: -Number.MAX_VALUE};

        _.each(nodes, function (node) {

            if (node.y < (topLeft.y && topRight.y)) {
                topLeft.y = topRight.y = node.y;
            }
            if (node.y > (botLeft.y && botRight.y)) {
                botLeft.y = botRight.y = node.y;
            }
            if (node.x < (topLeft.x && botLeft.x)) {
                topLeft.x = botLeft.x = node.x;
            }
            if (node.x > (topRight.x && botRight.x)) {
                topRight.x = botRight.x = node.x;
            }
        });

        var dimensions = {
            width: Math.abs(botLeft.x - topRight.x),
            height: Math.abs(botRight.y - topLeft.y)
        };

        var center = {
            xCenter: (topLeft.x + botRight.x) / 2,
            yCenter: (topRight.y + botLeft.y) / 2
        };

        return _.extend({
            topLeft: topLeft,
            topRight: topRight,
            botLeft: botLeft,
            botRight: botRight
        }, dimensions, center);
    }


    function getTrafficCSSforLink(link) {
        var inCss;
        var outCss;

        if (link.traffic !== undefined && !_.isEmpty(link.traffic)) {

            if (_.isArray(link.edges)) {
                inCss = _.max(link.traffic.edges, function (edge) {
                    return edge.source.load_in_percent;
                }).source.css;
                outCss = _.max(link.traffic.edges, function (edge) {
                    return edge.target.load_in_percent;
                }).target.css;
            } else {
                inCss = link.traffic.traffic_data.source.css;
                outCss = link.traffic.traffic_data.target.css;
            }

            if (!inCss) {
                inCss = UndefinedLoad;
            }
            if (!outCss) {
                outCss = UndefinedLoad;
            }

        } else {
            inCss = UndefinedLoad;
            outCss = UndefinedLoad;
        }

        return [
            {percent: 0, css: inCss},
            {percent: 50, css: inCss},
            {percent: 51, css: outCss},
            {percent: 100, css: outCss}
        ];
    }

    return GraphView;
});
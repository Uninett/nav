define([
    'netmap/graph',
    'netmap/models',
    'netmap/graph_info_view',
    'plugins/fullscreen',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/d3.min'
], function (Graph, Models, GraphInfoView, Fullscreen) {

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
            'netmap:removeFilter': 'removeRoomOrLocationFilter',
            'netmap:selectedVlanChanged': 'updateSelectedVlan',
            'netmap:updateGraph': 'update',
            'netmap:refreshGraph': 'refresh',
            'netmap:searchGraph': 'search',
            'netmap:saveNodePositions': 'saveNodePositions',
            'netmap:zoomToExtent': 'zoomToExtent',
            'netmap:resetTransparency': 'resetTransparency',
            'netmap:resetZoom': 'resetZoom',
            'netmap:fixNodes': 'fixNodes',
            'netmap:unfixNodes': 'unfixNodes',
            'netmap:toggleForce': 'toggleForce'
        },

        initialize: function () {
            this.w = this.$el.width();
            this.h = $(window).height();

            // Initial d3 graph state
            this.force = d3.layout.force()
                .gravity(0.1)
                .charge(-2500)
                .linkDistance(250)
                .size([this.w, this.h]);

            this.forceEnabled = false;
            this.nodes = this.force.nodes();
            this.links = this.force.links();
            this.isLoadingForTheFirstTime = true;

            Backbone.EventBroker.register(this);

            this.model = new Graph();
            this.netmapView = this.options.netmapView;

            this.model.set("locations", this.netmapView.filterStrings);

            // Indicators
            this.indicatorHolder = this.createIndicatorHolder();
            this.loadingGraphIndicator = this.createLoadingGraphIndicator();
            this.loadingGraphIndicator.appendTo(this.indicatorHolder).hide();
            this.loadingTrafficIndicator = this.createLoadingTrafficIndicator();
            this.loadingTrafficIndicator.appendTo(this.indicatorHolder).hide();
            this.listenTo(this.model, 'change:loadingTraffic', this.toggleLoadingTraffic);

            this.graphInfoView = new GraphInfoView({parent: this.el});

            this.initializeDOM();
            this.bindEvents();
            this.initializeNetmapView();
            this.fetchGraphModel();
        },


        createIndicatorHolder: function() {
            return $('<div>')
                .css({
                    position: 'absolute',
                    top: '10px',
                    left: '10px'
                })
                .appendTo(this.el);
        },


        createLoadingGraphIndicator: function() {
            return $('<div class="alert-box info">')
                .css({ width: '200px' })
                .html('Loading graph');
        },


        createLoadingTrafficIndicator: function() {
            return $('<div class="alert-box info">')
                .css({ width: '200px' })
                .html('Loading traffic data');
        },


        toggleLoadingTraffic: function() {
            if (this.model.get('loadingTraffic') === true) {
                console.log('We are loading traffic');
                this.loadingTrafficIndicator.show();
            } else {
                console.log('We stopped loading traffic');
                this.loadingTrafficIndicator.hide('slow');
            }
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

            var zoomParts = this.getTranslationsAndScale();
            this.netmapView.baseZoom = zoomParts;
            this.trans = zoomParts[0];
            this.scale = zoomParts[1];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);

            var selectedCategories = this.netmapView.get('categories');
            _.each(this.model.get('filter_categories'), function (category) {
                category.checked = _.indexOf(selectedCategories, category.name) >= 0;
            });
        },

        addFullscreenToggler: function () {
            var self = this;

            if (Fullscreen.isFullscreenSupported()) {
                var fullscreenToggler = $('<button class="tiny"><i class="fa fa-arrows-alt fa-lg"></i></button>');
                fullscreenToggler.css({
                    'position': 'absolute',
                    'right': '10px',
                    'top': '10px'
                });
                this.$el.append(fullscreenToggler);
                fullscreenToggler.on('click', function () {
                    Fullscreen.toggleFullscreen(self.el);
                });
            }
        },

        getTranslationsAndScale: function() {
            var zoomParts = this.netmapView.get('zoom').split(';');
            var translations = this.getTranslations(zoomParts[0]);
            var scale = this.getScale(zoomParts[1]);
            return [translations, scale];
        },

        /**
         * Get translation or set sensible defaults
         */
        getTranslations: function(zoom) {
            var translations = zoom.split(',');
            if (isNaN(translations[0]) || isNaN(translations[1])) {
                translations = ["0","0"];
            }
            return translations;
        },

        /**
         * Get scale or set sensible default
         */
        getScale: function(scale) {
            return +scale ? scale : "0.5";
        },

        /**
         * Initialize the SVG DOM elements
         */
        initializeDOM: function () {
            this.addFullscreenToggler();

            this.svg = d3.select(this.el)
                .append('svg')
                .attr('width', this.w)
                .attr('height', this.h)
                .attr('viewBox', '0 0 ' + this.w + ' ' + this.h)
                .attr('pointer-events', 'all')
                .attr('overflow', 'hidden');

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
            this.zoom = d3.behavior.zoom().center([this.w / 2, this.h / 2]);
            this.svg.call(this.zoom.on('zoom', function () {
               self.zoomCallback.call(self);
            }));

            // Set up node dragging listener
            this.drag = d3.behavior.drag()
                .on('dragstart', function (node) {
                    self.dragStart.call(this, node, self);
                })
                .on('drag', function (node) {
                    self.dragMove.call(this, node, self);
                })
                .on('dragend', function (node) {
                    self.dragEnd.call(this, node, self);
                });

            // Set up resize on window resize
            $(window).resize(function () {
                self.w = self.$el.width();
                self.h = $(window).height();
                self.svg.attr('width', self.w)
                    .attr('height', self.h);
            });

            // Set up tick event
            this.force.on('tick', function () {
                self.tick.call(self);
            });
        },

        tick: function () {

            this.link.attr('x1', function (o) {
                return o.source.x;
            }).attr('y1', function (o) {
                return o.source.y;
            }).attr('x2', function (o) {
                return o.target.x;
            }).attr('y2', function (o) {
                return o.target.y;
            });

            this.node.attr('transform', function(o) {
                return 'translate(' + o.x + "," + o.y + ')';
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
            if (this.netmapView.filterStrings.length) {
                nodes = filterNodesByRoomsOrLocations(nodes, this.netmapView.filterStrings);
                links = filterLinksByRoomsOrLocations(links, this.netmapView.filterStrings);
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
                    node.x = node.position.x;
                    node.y = node.position.y;
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
            // Make sure the rendered nodes are evenly distributed
            this.forceEnabled = true;
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
                .attr('opacity', 1);


            this.link.exit().transition()
                .duration(TransitionDuration)
                .style('opacity', 0)
                .remove();

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
                .call(this.drag);

            nodeElement.append('image')
                .attr('xlink:href', function (o) {
                    return '/static/images/netmap/' + o.category.toLowerCase() + '.png';
                })
                .attr('x', -16)
                .attr('y', -16)
                .attr('width', 32)
                .attr('height', 32);

            nodeElement.append('text')
                .attr('class', 'sysname')
                .attr('dy', '1.5em')
                .attr('text-anchor', 'middle')
                .text(function (o) {
                    return o.sysname;
                });

            nodeElement.attr('opacity', 0)
                .transition()
                .duration(TransitionDuration)
                .style('opacity', 1);

            this.node.exit()
                .transition()
                .duration(TransitionDuration)
                .style('opacity', 0)
                .remove();

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
                .attr('y2', '100%');

            var stops = gradient.selectAll('stop')
                .data(getTrafficCSSforLink);
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

            if (this.netmapView.refreshTrafficOnly) {
                this.model.loadTraffic(this.netmapView.filterStrings);
            } else {
                this.fetchGraphModel();
            }
        },

        fetchGraphModel: function () {

            var self = this;

            this.loadingGraphIndicator.show();
            this.graphInfoView.reset();

            var jqxhr = this.model.fetch({
                success: function () {
                    self.update();
                    self.model.loadTraffic(self.netmapView.filterStrings);
                },
                error: function () { // TODO: Use alert message instead
                    alert('Error loading graph, please try to reload the page');
                }
            });

            jqxhr.always(function() {
                self.loadingGraphIndicator.hide('slow');
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
            this.model.set("locations", this.netmapView.filterStrings);

            var zoomParts = this.getTranslationsAndScale();
            this.netmapView.baseZoom = zoomParts;
            this.trans = zoomParts[0];
            this.scale = zoomParts[1];
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

        toggleForce: function (statusOn) {
            if (statusOn) {
                this.force.stop();
            } else {
                this.force.resume();
            }
            this.forceEnabled = !this.forceEnabled;
        },

        addFilterString: function (filter) {
            this.netmapView.filterStrings.push(filter);
            this.model.set("locations", this.netmapView.filterStrings);
            this.update();
        },

        removeRoomOrLocationFilter: function (filter) {
            this.netmapView.filterStrings = _.without(
                this.netmapView.filterStrings, filter.toString());
            this.update();
        },

        saveNodePositions: function (model, state, alertContainer) {

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

                console.log("Saving dirty nodes", dirtyNodes);

                var nodePositions = new Models.NodePositions().set({
                    'data': dirtyNodes,
                    'viewid': this.netmapView.id
                });

                nodePositions.save(nodePositions.get('data'), {
                    success: function () {
                        console.log('Node positions saved');
                        // Notify control view of change, so it can display a green
                        // "updated" box to the user
                        Backbone.EventBroker.trigger('netmap:saveSuccessful', model, state, alertContainer);
                    },
                    error: function (model, resp, opt) {
                        console.log("Failed", resp.responseText);
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

        zoomToExtent: function () {
            var bounds = findBoundingBox(this.nodes);
            this.transformGraphFromBounds(bounds);
            this.netmapView.set('zoom', this.trans.join(',') + ';' + this.scale);
        },

        resetTransparency: function () {
            this.render();
        },

        resetZoom: function () {
            var zoomParts = this.netmapView.baseZoom;
            this.trans = zoomParts[0];
            this.scale = zoomParts[1];
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);
            this.transformGraphTransition();
        },

        unfixNodes: function () {

            _.each(this.nodes, function (node) {
                node.fixed = false;
            });
            if (this.forceEnabled) {
                console.log("resume force");
                this.force.resume();
            }
        },

        fixNodes: function () {
            console.log("Fixing nodes");
            _.each(this.nodes, function (node) {
                node.fixed = true;
            });
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
                   .attr('transform',
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
        },

        dragMove: function(node, self) {
            node.px += d3.event.dx;
            node.py += d3.event.dy;
            node.x += d3.event.dx;
            node.y += d3.event.dy;
            node.fixed = true;
            self.tick();
        },

        dragEnd: function (node, self) {
            d3.select(this).select('circle').remove();
            if (self.forceEnabled) {
                self.force.resume();
            }
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
        return _.filter(nodes, function (node) {
            return _.some(filters, function (filter) {
                return filter === node.roomid || filter === node.locationid;
            });
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

        return _.filter(links, function (link) {
            return (_.contains(filters, link.source.roomid) && _.contains(filters, link.target.roomid) ||
                _.contains(filters, link.source.locationid) && _.contains(filters, link.target.locationid));
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
        if (_.isArray(link.edges)) {
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
        var inCss = UndefinedLoad;
        var outCss = UndefinedLoad;

        if (link.traffic !== undefined && !_.isEmpty(link.traffic)) {

            if (_.isArray(link.edges)) {
                inCss = _.max(link.traffic.edges, function (edge) {
                    return edge.source.load_in_percent;
                }).source.css;
                outCss = _.max(link.traffic.edges, function (edge) {
                    return edge.target.load_in_percent;
                }).target.css;
            } else if (link.traffic.traffic_data !== undefined) {
                inCss = link.traffic.traffic_data.source.css;
                outCss = link.traffic.traffic_data.target.css;
            }

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

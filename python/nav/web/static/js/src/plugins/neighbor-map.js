define(function (require, exports, module) {

    var d3 = require('d3v4');
    var _ = require('libs/underscore');

    function NeighborMap(node) {
        this.motherNode = d3.select(node);  // Use this for selecting prior to svg
        this.netboxid = parseInt(this.motherNode.attr('data-netboxid'), 10);
        if (!this.netboxid) {
            console.log('No netboxid found');
            return;
        }

        /* Size of svg container */
        this.width = 800;
        this.height = 700;

        /* Node and link properties */
        this.linkDistance = 250;
        var imagePath = NAV.imagePath + '/netmap';
        this.nodeImages = {
            'GSW': imagePath + '/gsw.png',
            'SW': imagePath + '/sw.png',
            'GW': imagePath + '/gw.png',
            'ELINK': imagePath + '/elink.png',
            'EDGE': imagePath + '/edge.png',
            'OTHER': imagePath + '/other.png',
            'SRV': imagePath + '/srv.png',
            'WLAN': imagePath + '/wlan.png',
            'UNRECOGNIZED': imagePath + '/unrecognized.png'
        };

        this.selectors = {
            nodes: '.node',
            links: 'line.link',
            linkLabelFromCenter: '.linkLabelFromCenter',
            linkLabelToCenter: '.linkLabelToCenter'
        };

        this.filterForm = $('#neighbor-category-filters');
        this.initialize();
        this.activatePanel();
        this.fetchData();
    }

    NeighborMap.prototype = {
        /** Create svg element */
        initialize: function () {
            this.svg = this.motherNode.append("svg")
                           .attr("width", this.width)
                           .attr("height", this.height)
                           .style("border", '1px solid black');
            /* The order of the elements in the dom determines what is drawn
            above other stuff. To make sure nodes always are at the top and
            links always are on the bottom we put them into groups.*/
            this.svg.append("g").attr("id", "links");
            this.svg.append("g").attr("id", "linklabels");
            this.svg.append("g").attr("id", "nodes");
        },

        activatePanel: function () {
            this.filterForm.on('change', this.render.bind(this));
        },

        /** Fetch neighbourhood data for this netbox */
        fetchData: function () {
            var self = this;
            d3.json('/ajax/open/neighbormap/' + this.netboxid, function (json) {
                if (json) {
                    // Filter duplicates
                    json.nodes = _.uniq(json.nodes, function(node) { return node.netboxid; });

                    self.data = json;
                    self.render();
                }
            });
        },

        /** Indicates if this node is the special focusnode */
        isFocusNode: function(node) {
            return node.netboxid === this.netboxid;
        },

        /** Create and display all objects and svg elements */
        render: function () {
            var data = this.data;

            data = this.filterByCategories(data, this.getCategories());

            this.setCenterNode(data.nodes);
            this.createSvgNodes(data.nodes);
            this.createSvgLinks(data.links);
            this.createLinkLabels(data.links);
            this.createSimulation(data);
        },

        getCategories: function() {
            var categories = []
            this.filterForm.find('[type=checkbox]:checked').each(function(index, element) {
                categories.push(element.value);
            });
            return categories;
        },

        /** Filter nodes based on categories */
        filterByCategories: function (data, categories) {
            var self = this;

            var nodeLookup = {};  // Temporary lookup for nodes
            data.nodes.forEach(function(node) {
                nodeLookup[node.netboxid] = node;
            });

            return {
                'nodes': data.nodes.filter(function(node) {
                    return _.contains(categories, node.category) || node.netboxid === self.netboxid;
                }),
                'links': data.links.filter(function(link) {
                    if (link.target.category) {
                        return _.contains(categories, link.target.category);
                    } else {
                        return _.contains(categories, nodeLookup[link.target].category);
                    }
                })
            };
        },

        /** Sets the node to be in the center */
        setCenterNode: function(nodes) {
            var centerNode = _.find(nodes, this.isFocusNode.bind(this));
            centerNode.fx = this.width / 2;
            centerNode.fy = this.height / 2;
        },

        /** Create all the visible links between the nodes */
        createSvgLinks: function (dataLinks) {
            var svgLinks = this
                .svg
                .select('#links')
                .selectAll(this.selectors.links)
                .data(dataLinks, function(d) {
                    return d.target.netboxid ? d.target.netboxid : d.target;
                });
            var svgLinksEnter = svgLinks
                .enter()
                .append('line')
                .attr('class', 'link')
                .style('stroke-width', function (link) {
                    var strokeWidth = 2;
                    if (link.ifname.length > 1) {
                        strokeWidth = 4;
                    }
                    return strokeWidth;
                })
                .style('stroke', '#ddd');
            svgLinks.exit().remove();

            this.svgLinks = svgLinks.merge(svgLinksEnter);
        },

        /** Create the link labels, in this case interface names */
        createLinkLabels: function (dataLinks) {
            var svgLinkLabelFromCenter, svgLinkLabelToCenter;

            svgLinkLabelFromCenter = this
                .svg
                .select('#linklabels')
                .selectAll(this.selectors.linkLabelFromCenter)
                .data(dataLinks, function(d) {
                    return d.target.netboxid ? d.target.netboxid : d.target;
                });

            svgLinkLabelFromCenter
                .enter()
                .append('g')
                .attr('class', 'linkLabelFromCenter')
                .append('text')
                .style('font-size', '0.8em')
                .attr('text-anchor', 'middle')
                .text(function (link) {
                    return link.ifname;
                });
            svgLinkLabelFromCenter.exit().remove();

            svgLinkLabelToCenter = this
                .svg
                .select('#linklabels')
                .selectAll(this.selectors.linkLabelToCenter)
                .data(dataLinks, function(d) {
                    return d.target.netboxid ? d.target.netboxid : d.target;
                });

            svgLinkLabelToCenter
                .enter()
                .append('g')
                .attr('class', 'linkLabelToCenter')
                .append('text')
                .style('font-size', '0.8em')
                .attr('text-anchor', 'middle')
                .text(function (link) {
                    return link.to_ifname;
                });
            svgLinkLabelToCenter.exit().remove();

            this.svgLinkLabelFromCenter = this.svg.selectAll(this.selectors.linkLabelFromCenter);
            this.svgLinkLabelToCenter = this.svg.selectAll(this.selectors.linkLabelToCenter);
        },

        /** Create all the visible nodes */
        createSvgNodes: function (dataNodes) {
            var self = this,
                svgNodes = this
                    .svg.select('#nodes')
                    .selectAll(this.selectors.nodes)
                    .data(dataNodes, function (node) {
                        return node.netboxid;
                    }),
                newNodes = svgNodes
                    .enter()
                    .append('g')
                    .attr('class', 'node');

            svgNodes.exit().remove();

            this.svgNodes = svgNodes.merge(newNodes);
            // Reorder nodes to make sure new lines does not overwrite old nodes
            this.svgNodes.order();

            this.appendImagesToNodes(newNodes);
            this.appendTextToNodes(newNodes);
            this.appendClickListeners(newNodes);
        },

        createSimulation: function(data) {
            var simulation = d3.forceSimulation(data.nodes)
                    .force('aversion', d3.forceCollide(50))
                    .force('links', d3.forceLink(data.links)
                           .distance(this.linkDistance)
                           .id(function(d) {return d.netboxid;}));

            if (data.nodes.length > 2) {
                simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            }

            simulation.on('tick', this.tick.bind(this));

            this.addDrag(simulation);
        },

        /** Update all positions for each tick of the force algorithm */
        tick: function () {
            var self = this;

            this.svgLinks
                .attr('x1', function (link) { return link.source.x; })
                .attr('y1', function (link) { return link.source.y; })
                .attr('x2', function (link) { return link.target.x; })
                .attr('y2', function (link) { return link.target.y; });

            this.svgLinkLabelFromCenter.attr('transform', function (link) {
                return self.calculateLinePoint(link.source, link.target, self.getLabelDistance(link));
            });

            this.svgLinkLabelToCenter.attr('transform', function (link) {
                return self.calculateLinePoint(link.target, link.source, 50);
            });

            this.svgNodes.attr("transform", function (node) {
                return "translate(" + node.x + "," + node.y + ")";
            });
        },

        /** Append the correct images to the nodes */
        appendImagesToNodes: function (svgNodes) {
            var self = this;
            svgNodes.append('image')
                .attr('xlink:href', function (node) {
                    return self.nodeImages[node.category];
                })
                .attr("x", -16)
                .attr("y", -16)
                .attr('width', 32)
                .attr('height', 32)
                .style('cursor', 'pointer');
        },

        /** Append correct text to the nodes */
        appendTextToNodes: function (svgNodes) {
            svgNodes.append("text")
                .attr("dx", -16)
                .attr("dy", 25)
                .attr("text-anchor", "middle")
                .text(function (node) {
                    return node.name;
                });
        },

        /** Go to other page when node is clicked */
        appendClickListeners: function (svgNodes) {
            var self = this;
            svgNodes.on('click', function (node) {
                if (node.category !== self.unrecognized) {
                    location.href = '/ipdevinfo/' + node.sysname + '/#!neighbors';
                }
            });
        },

        /**
         * Given source and target coords - calculate a point along the line
         * between source and target with length 'distance' from the source
         */
        calculateLinePoint: function (source, target, distance) {
            var m, x, y,
                x0 = source.x,
                x1 = target.x,
                y0 = source.y,
                y1 = target.y;

            m = (y1 - y0) / (x1 - x0);  // Line gradient
            if (x0 < x1) {
                x = x0 + (distance / Math.sqrt(1 + (m * m)));
            } else {
                x = x0 - (distance / Math.sqrt(1 + (m * m)));
            }
            y = m * (x - x0) + y0;
            return "translate(" + x + ',' +  y + ')';
        },
        getLabelDistance: function (link) {
            var baseDistance = 70,
                ifnameBasedDistance = baseDistance * (1 + (link.ifname.length - 1) * 0.3);
            return ifnameBasedDistance < this.linkDistance ? ifnameBasedDistance : this.linkDistance;
        },

        /** Add drag behaviour to nodes */
        addDrag: function(simulation) {
            function dragStarted(d) {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragging(d) {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
            }

            function dragEnded(d) {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }

            var self = this;
            this.svgNodes.call(
                d3.drag()
                    .filter(function(node) {
                        // Set focus node to not be draggable
                        return !self.isFocusNode(node);
                    })
                    .on('start', dragStarted)
                    .on('drag', dragging)
                    .on('end', dragEnded)
            );
        }
    };


    return NeighborMap;

});

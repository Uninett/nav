define(["libs/d3.v2"], function () {

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

        this.unrecognized = 'UNRECOGNIZED';

        this.unrecognizedToggler = d3.select('#unrecognized');
        this.initialize();
        this.activatePanel();
        this.fetchData();
    }

    NeighborMap.prototype = {
        initialize: function () {
            /* Create svg element and define force algorithm */
            this.createSvg();
            this.defineForceAlgorithm();
        },
        createSvg: function () {
            this.svg = this.motherNode.append("svg")
                .attr("width", this.width)
                .attr("height", this.height)
                .style("border", '1px solid black');
        },
        defineForceAlgorithm: function () {
            this.force = d3.layout.force()
                .charge(-500)
                .friction(0.7)
                .linkDistance(this.linkDistance)
                .size([this.width, this.height]);
        },
        activatePanel: function () {
            var that = this;
            this.unrecognizedToggler.on('change', function () {
                that.render();
            });
        },
        fetchData: function () {
            /* Fetch neighbourhood data for this netbox */
            var that = this;
            d3.json('/ajax/open/neighbormap/' + this.netboxid, function (json) {
                if (json) {
                    that.data = json;
                    that.render();
                }
            });
        },
        render: function () {
            /* Create and display all objects and svg elements */
            var that = this,
                data = this.data;

            this.updateNodes(data.nodes);
            this.updateLinks(data.links);

            if (!this.unrecognizedToggler.property('checked')) {
                data = this.filterUncategorized();
            }

            this.force.nodes(data.nodes).links(data.links).start();
            this.createSvgLinks(data.links);
            this.createLinkLabels(data.links);
            this.createSvgNodes(data.nodes);

            this.force.on('tick', function () {
                that.tick.call(that);
            });
        },
        updateNodes: function (nodes) {
            /* Update all datanodes and a hash used when creating the links */
            var i, l, node;

            this.nodeHash = {};
            for (i = 0, l = nodes.length; i < l; i++) {
                node = nodes[i];
                if (node.netboxid === this.netboxid) {
                    node.fixed = true;  // Fix the main node
                }
                node.x = node.x || this.width / 2;
                node.y = node.y || this.height / 2;
                this.nodeHash[node.netboxid] = node;
            }
            return nodes;
        },
        updateLinks: function (links) {
            /* Set source and target for all links based on node hash */
            var i, l, link;
            for (i = 0, l = links.length; i < l; i++) {
                link = links[i];
                link.source = this.nodeHash[link.sourceId];
                link.target = this.nodeHash[link.targetId];
            }
            return links;
        },
        filterUncategorized: function () {
            var data = this.data,
                node,
                link,
                nodes = [],
                links = [];
            for (node in data.nodes) {
                if (data.nodes.hasOwnProperty(node) && data.nodes[node].category !== this.unrecognized) {
                    nodes.push(data.nodes[node]);
                }
            }
            for (link in data.links) {
                if (data.links.hasOwnProperty(link) && data.links[link].target.category !== this.unrecognized) {
                    links.push(data.links[link]);
                }
            }
            return {'nodes': nodes, 'links': links};
        },
        createSvgLinks: function (dataLinks) {
            /* Create all the visible links between the nodes */
            this.svgLinks = this.svg.selectAll('.link').data(dataLinks);
            this.svgLinks
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
            this.svgLinks.exit().remove();

        },
        createLinkLabels: function (dataLinks) {
            /* Create the link labels, in this case interface names */
            var svgLinkLabelFromCenter, svgLinkLabelToCenter;

            svgLinkLabelFromCenter = this.svg.selectAll('.linkLabelFromCenter').data(dataLinks);
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

            svgLinkLabelToCenter = this.svg.selectAll('.linkLabelToCenter').data(dataLinks);
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

            this.svgLinkLabelFromCenter = svgLinkLabelFromCenter;
            this.svgLinkLabelToCenter = svgLinkLabelToCenter;
        },
        createSvgNodes: function (dataNodes) {
            /* Create all the visible nodes */
            var that = this,
                svgNodes = this.svg.selectAll('.node')
                    .data(dataNodes, function (node) {
                        return node.netboxid;
                    }),
                newNodes = svgNodes
                    .enter()
                    .append('g')
                    .attr('class', function (node) {
                        return node.netboxid === that.netboxid ? node.category + ' node main' : node.category + ' node';
                    })
                    .call(this.force.drag);

            svgNodes.exit().remove();

            svgNodes.order();  // Reorder nodes to make sure new lines does not overwrite old nodes

            // Prevent dragging on main node
            this.svg.select('.node.main').on('mousedown.drag', null);

            this.appendImagesToNodes(newNodes);
            this.appendTextToNodes(newNodes);
            this.appendClickListeners(newNodes);
            this.svgNodes = svgNodes;
        },
        tick: function () {
            /* Update all positions for each tick of the force algorithm */
            var that = this;

            this.svgLinks
                .attr('x1', function (link) { return link.source.x; })
                .attr('y1', function (link) { return link.source.y; })
                .attr('x2', function (link) { return link.target.x; })
                .attr('y2', function (link) { return link.target.y; });

            this.svgLinkLabelFromCenter.attr('transform', function (link) {
                return that.calculateLinePoint(link.source, link.target, that.getLabelDistance(link));
            });

            this.svgLinkLabelToCenter.attr('transform', function (link) {
                return that.calculateLinePoint(link.target, link.source, 50);
            });

            this.svgNodes
                .attr('cx', function (node) { return node.x; })
                .attr('cy', function (node) { return node.y; });

            this.svgNodes.attr("transform", function (node) {
                return "translate(" + node.x + "," + node.y + ")";
            });
        },
        appendImagesToNodes: function (svgNodes) {
            /* Append the correct images to the nodes */
            var that = this;
            svgNodes.append('image')
                .attr('xlink:href', function (node) {
                    return that.nodeImages[node.category];
                })
                .attr("x", -16)
                .attr("y", -16)
                .attr('width', 32)
                .attr('height', 32)
                .style('cursor', 'pointer');
        },
        appendTextToNodes: function (svgNodes) {
            /* Append correct text to the nodes */
            svgNodes.append("text")
                .attr("dx", -16)
                .attr("dy", 25)
                .text(function (node) {
                    return node.name;
                });
        },
        appendClickListeners: function (svgNodes) {
            var that = this;
            svgNodes.on('click', function (node) {
                if (node.category !== that.unrecognized) {
                    location.href = '/ipdevinfo/' + node.sysname + '/#!neighbors';
                }
            });
        },
        calculateLinePoint: function (source, target, distance) {
            /*
             Given source and target coords - calculate a point along the line
             between source and target with length 'distance' from the source
             */
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
        }
    };


    return NeighborMap;

});

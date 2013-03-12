define(["libs/jquery", "libs/d3.v2"], function () {

    function NeighbourMap(node) {
        this.node = node;
        this.netboxid = $(this.node).attr('data-netboxid');
        if (!this.netboxid) {
            console.log('No netboxid found');
            return;
        }

        /* Size of svg container */
        this.width = 600;
        this.height = 400;

        /* Node and link properties */
        this.linkDistance = 120;
        this.nodeImages = {
            'GSW': '/images/netmap/gsw.png',
            'SW': '/images/netmap/sw.png',
            'GW': '/images/netmap/gw.png'
        };

        this.initialize();
        this.fetchData();
        this.render();
    }

    NeighbourMap.prototype = {
        initialize: function () {
            /* Create svg element and define force algorithm */
            this.createSvg();
            this.defineForceAlgorithm();
        },
        createSvg: function () {
            this.svg = d3.select(this.node).append("svg")
                .attr("width", this.width)
                .attr("height", this.height);
        },
        defineForceAlgorithm: function() {
            this.force = d3.layout.force()
                .charge(-10)
                .linkDistance(this.linkDistance)
                .size([this.width, this.height]);
        },
        fetchData: function () {
            /* Fetch neibourhood data for this netbox */
            this.data = {
                "nodes": [
                    {netboxid: 35, 'sysname': 'uninett-gw', 'category': 'GSW'},
                    {netboxid: 560, 'sysname': 'teknobyen-5etg-sw1', 'category': 'GW'},
                    {netboxid: 540, 'sysname': 'teknobyen-5etg-sw2', 'category': 'SW'}
                ],
                "links": [
                    {"sourceId": 35, "targetId": 560},
                    {"sourceId": 35, "targetId": 540}
                ]
            };
        },
        render: function () {
            /* Create and display all objects and svg elements */
            var that = this,
                dataNodes = this.updateNodes(),
                dataLinks = this.updateLinks();

            this.force.nodes(dataNodes).links(dataLinks).start();
            this.createSvgLinks(dataLinks);
            this.createSvgNodes(dataNodes);

            this.force.on('tick', function () {
                that.tick.call(that);
            });
        },
        updateNodes: function () {
            /* Update all datanodes and a hash used when creating the links */
            var nodes = this.data.nodes;
            this.nodeHash = {};
            for (var i=0, node; node=nodes[i]; i++) {
                if (node.netboxid == this.netboxid) {
                    node.fixed = true;  // Fix the main node
                }
                node.x = this.width / 2;
                node.y = this.height / 2;
                this.nodeHash[node.netboxid] = node;
            }
            return nodes;
        },
        updateLinks: function () {
            /* Set source and target for all links based on node hash */
            var links = this.data.links;
            for (var i=0, link; link=links[i]; i++) {
                link.source = this.nodeHash[link.sourceId];
                link.target = this.nodeHash[link.targetId];
            }
            return links;
        },
        createSvgLinks: function (dataLinks) {
            /* Create all the visible links between the nodes */
            this.svgLinks = this.svg.selectAll('.link')
                .data(dataLinks)
                .enter()
                .append('line')
                .attr('class', '.link')
                .style('stroke-width', 2)
                .style('stroke', '#999');
        },
        createSvgNodes: function (dataNodes) {
            /* Create all the visible nodes */
            var svgNodes = this.svg.selectAll('.node')
                .data(dataNodes, function (node) {
                    return node.netboxid;
                })
                .enter()
                .append('g')
                .attr('class', '.node')
                .call(this.force.drag);

            this.appendImagesToNodes(svgNodes);
            this.appendTextToNodes(svgNodes);
            this.svgNodes = svgNodes;
        },
        tick: function () {
            /* Update all positions for each tick of the force algorithm */
            this.svgLinks
                .attr('x1', function (link) { return link.source.x; })
                .attr('y1', function (link) { return link.source.y; })
                .attr('x2', function (link) { return link.target.x; })
                .attr('y2', function (link) { return link.target.y; });

            this.svgNodes
                .attr('cx', function (node) { return node.x; })
                .attr('cy', function (node) { return node.y; });

            this.svgNodes.attr("transform", function(node) {
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
                .attr('height', 32);
        },
        appendTextToNodes: function (svgNodes) {
            /* Append correct text to the nodes */
            svgNodes.append("text")
                .attr("dx", 25)
                .attr("dy", "0.3em")
                .text(function (node) {
                    return node.sysname;
                })
        }

    };

    return NeighbourMap;

});

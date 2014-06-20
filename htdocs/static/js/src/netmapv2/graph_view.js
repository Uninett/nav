define([
    'netmap/graph',
    'plugins/d3force',
    'libs/jquery',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/d3.v2'
], function (Graph, D3ForceHelper) {

    var GraphView = Backbone.View.extend({

        el: '#graph-view',

        interests: {
            'netmap:topologyLayerChanged': 'updateTopologyLayer',
            'netmap:netmapViewChanged': 'updateNetmapView',
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
                .linkDistance(150)
                .size([this.w, this.h])
                ;

            this.nodes = this.force.nodes();
            this.links = this.force.links();
            this.forceHelper = new D3ForceHelper(this.nodes, this.links);

            this.svg = d3.select(this.el)
                .append('svg')
                .attr('width', this.w)
                .attr('height', this.h)
                .attr('viewBox', '0 0 ' + this.w + ' ' + this.h)
                .attr('overflow', 'hidden')
                ;

            this.model = new Graph();

            Backbone.EventBroker.register(this);

            this.bindEvents();

            this.model.fetch();
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
        },

        reset: function () { console.log('graph view reset');

            //this.
        },

        update: function () { console.log('graph view update');

            // You wouldn't want this running
            // while updating
            this.force.stop();

            var nodes = this.model.get('nodeCollection').getGraphObjects();
            var vlans = this.model.get('vlanCollection').getGraphObjects();
            var links = this.model.get('linkCollection').getGraphObjects();

            nodes = nodes.concat(vlans);

            this.force
                .nodes(nodes)
                .links(links)
                ;

            console.log(nodes.length);

            this.render(nodes, links);

            this.force.start();
        },

        render: function (nodes, links) { console.log('graph view render');

            this.link = this.svg.selectAll('.link')
                .data(links)
                .enter()
                .append('line')
                //.append('path') For curved lines
                .attr('class', 'link')
                .attr('stroke', function (o) {
                    // TODO: Load based
                    return '#000000';
                })
                ;

            this.node = this.svg.selectAll('.node')
                .data(nodes)
                .enter()
                .append('g')
                .attr('class', 'node')
                .on('dblclick', this.dblclick)
                .call(this.force.drag)
                ;

            this.node.append('image')
                .attr('xlink:href', function (o) {
                    return '/static/images/netmap/' + o.category.toLowerCase() + '.png';
                })
                .attr('x', -16)
                .attr('y', -16)
                .attr('width', 32)
                .attr('height', 32)
                ;

            this.node.append('text')
                .attr('class', 'sysname')
                .attr('dy', '1.5em')
                .attr('text-anchor', 'middle')
                .text(function (o) {
                    return o.sysname;
                })
                ;

            // Set up tick event
            var self = this;
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

        updateTopologyLayer: function (layer) { console.log('graph view update topology');

            this.model.set('layer', layer);
            this.model.fetch();
        },

        updateNetmapView: function (view) { console.log('graph view update view');

            // TODO
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

    return GraphView;
});
define([
    'plugins/netmap-extras',
    'netmap/resource',
    'netmap/models/graph',
    'netmap/models/map',
    'netmap/models/default_map',
    'netmap/views/loading_spinner',
    // Pull in the Collection module from above
    'libs-amd/text!netmap/templates/draw_map.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapExtras, Resources, GraphModel, MapModel, DefaultMapModel, LoadingSpinnerView, netmapTemplate) {

    var drawNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "chart",

        broker: Backbone.EventBroker,
        interests: {
            'netmap:changeTopology': 'setMapPropertyTopology',
            'netmap:changePosition': 'setMapPropertyPositionFilter',
            'netmap:changeDisplayTopologyErrors': 'setMapPropertyDisplayTopologyErrors',
            'netmap:ui:mouseover': 'setUIMouseOver',
            'netmap:selectVlan': 'setUIVLANSelection',
            'netmap:stopLayoutForceAlgorithm': 'stopLayoutForce',
            'netmap:node:setFixed': 'setGraphNodeFixedStatus',
            'netmap:nodes:setFixed': 'setGraphNodesCollectionFixedStatus',
            'netmap:search': 'search',
            'netmap:centerGraph': 'centerGraph',
            'netmap:resize:animate': 'resizeAnimate',
            'netmap:changeActiveMapProperty': 'setMapProperty',
            'netmap:request:graph': 'broadcastGraphCopy',
            'headerFooterMinimize:trigger': 'resize'
        },
        initialize: function () {
            // Settings
            this.imagesPrefix = "/images/netmap/";

            // Initial states
            this.isGraphLoadingForFirstTime = true;
            this.trans = [0,0];
            this.scale = 1;
            this.zoom = d3.behavior.zoom();

            this.selected_node = null;
            this.selected_vlan = null;
            this.ui = {
                'mouseover': {
                    'nodes': false,
                    'links': false
                }
            };


            this.svg = null;
            this.$el.append(netmapTemplate);
            this.showLoadingSpinner(true);

            if (!this.options.mapProperties) {
                this.options.mapProperties = Resources.getMapProperties();
            }

            this.w = this.options.cssWidth;
            this.resize({width: this.w});

            this.force = d3.layout.force().gravity(0.1).charge(-2500).linkDistance(250).size([this.w, this.h]);
            this.nodes = this.force.nodes();
            this.links = this.force.links();

            // swap .on with .bind for jQuery<1.7
            $(window).on("resize.app", _.bind(this.resize, this));

            this.model = new GraphModel({
              id: this.options.mapProperties.get('viewid', this.options.viewid),
              topology: this.options.mapProperties.get('topology', 2)
            });

            this.initializeDOM();

            this.loadTopologyGraph();

            this.broker.register(this);
            this.bindMapProperties();
        },
        initializeDOM: function () {
            var self = this;
            // fixes standard structure in svg.
            // <svg>
            //   <rect (background)
            //   <g>
            //     <g id=boundingbox
            //        <g class=links
            //        <g class=nodes
            // ...
            var vis = this.vis = d3.select(this.el)
                .append("svg:svg")
                .attr('id', 'svg-netmap')
                .attr("width", this.w).attr("height", this.h)
                .attr("pointer-events", "all")
                .attr("overflow", "hidden");
            vis.append('svg:rect')
                .attr('width', this.w)
                .attr('height', this.h)
                .attr('fill', 'white')
                .call(this.zoom.on("zoom", function () { self.zoomRescale.call(self);}));
            var root = vis.append("svg:g");
            var bounding_box = this.bounding_box = root
                .append('svg:g')
                .attr('id', 'boundingbox');


            // Grouping elements
            this.linkErrorsGroupRoot = bounding_box.append("g").attr("class", "linksmeta");
            var selectedNodeGroupRoot = this.selectedNodeGroupRoot = bounding_box.append("g").attr("class", "selected_nodes");
            var selectedLinkGroupRoot = this.selectedLinkGroupRoot = bounding_box.append("g").attr("class", "selected_links");
            this.linkGroupRoot = bounding_box.append("g").attr("class", "links");
            this.nodeGroupRoot = bounding_box.append("g").attr("class", "nodes");

            // Zero initalizes, so it doesn't crash on tick(). etc.
            this.nodesInVLAN = selectedNodeGroupRoot.selectAll("g circle").data([]);
            this.linksInVLAN = selectedLinkGroupRoot.selectAll("g line").data([]);

        },
        broadcastGraphCopy: function () {
            this.broker.trigger("netmap:graph", new GraphModel({ 'nodes': this.nodes, 'links': this.links }));
        },
        showLoadingSpinner: function (bool) {
            if (bool) {
                (this.$el).find('#svg-netmap').hide();

                this.spinnerView = new LoadingSpinnerView();
                this.$el.prepend(this.spinnerView.render().el);
            } else {
                if (this.spinnerView) {
                    this.spinnerView.close();
                    $(this.svg).show();
                }
            }
        },
        loadTopologyGraph: function (shouldRezoomAndTranslate) {
            var self = this;
            this.broker.trigger("netmap:graph:isDoneLoading", false);

            this.model.fetch({
                success: function (model) {
                    self.model = model;
                    var newModel = model.toJSON();

                    if (self.isGraphLoadingForFirstTime) {
                        _.each(newModel.nodes, function(d, i) {
                            self.addNode(d.data.sysname, d);
                        });
                        _.each(newModel.links, function (d) {
                            self.addLink(d.source, d.target, d.data);
                        });

                        self.zoomRescaleFromActiveProperty(self.options.mapProperties.get('zoom'));
                        self.isGraphLoadingForFirstTime = false;
                    } else {
                        self.updateTopologyGraph(newModel);
                    }

                    if (shouldRezoomAndTranslate) {
                        self.zoomRescaleFromActiveProperty(self.options.mapProperties.get('zoom'));
                    }
                    self.update(); // calls rest of the updateRender functions which updates the SVG.
                    self.broadcastGraphCopy();
                    self.broker.trigger("netmap:graph:isDoneLoading", true);
                },
                error: function () {
                    alert("Error loading graph, please try to reload the page");
                    self.broker.trigger("netmap:graph:isDoneLoading", true);
                }
            });
        },

        sysnameFromLinkObjectOrGraphModelFetch: function (source, target) {
            var sourceSysname = (_.isObject(source) ? source.data.sysname : source);
            var targetSysname = (_.isObject(target) ? target.data.sysname : target);
            return sourceSysname+"-"+targetSysname;
        },
        updateTopologyGraph: function (newTopologyGraphJSON) {
            var self = this;

            // nodes in this.nodes not present in newTopologyGraphJSON.nodes
            var toRemove = this.difference(this.nodes, newTopologyGraphJSON.nodes, function (a, b) {
                return a.data.sysname === b.data.sysname;
            });

            // nodes present in newTopologyGraphJSON.nodes and not in this.nodes
            var toAdd = this.difference(newTopologyGraphJSON.nodes, this.nodes, function (a, b) {
                return a.data.sysname === b.data.sysname;
            });


            // delete existing nodes not in new model json
            for (var i = 0; i < toRemove.length; i++) {
                var nodeToRemove = toRemove[i];
                this.removeNode(nodeToRemove.data.sysname);
            }

            for (var j = 0; j < toAdd.length; j++) {
                var nodeToAdd = toAdd[j];
                this.addNode(nodeToAdd.data.sysname, nodeToAdd);
            }


            // LINKS handling starts here
            // newTopologyGraphJSOn.links (source and target) is not objects
            // when comming from a GraphModel (model) fetch operation.



            // links to remove that are not present in newTopologyGraphJSON.links, but in this.links
            // (even if removeNode clears links from it, it might be that node is available in this.nodes
            // but should have it links removed...)
            var linksToRemove = this.difference(this.links, newTopologyGraphJSON.links, function (a, b) {
                return self.sysnameFromLinkObjectOrGraphModelFetch(b) === a.source.data.sysname+"-"+a.target.data.sysname;
            });

            for (var k = 0; k < linksToRemove.length; k++) {
                var kx = linksToRemove[k];
                this.removeLink(kx.source.data.sysname, kx.target.data.sysname);
            }

            // new links present in newTopologyGraphJSON.links add to this.links
            var linksToAdd = this.difference(newTopologyGraphJSON.links, this.links, function (a, b) {
                return self.sysnameFromLinkObjectOrGraphModelFetch(a) === b.source.data.sysname+"-"+b.target.data.sysname;
            });

            for (var m = 0; m < linksToAdd.length; m++) {
                var mx = linksToAdd[m];
                this.addLink(mx.source, mx.target, mx.data);
            }


            // Done adding new nodes and links, and removed non-existing nodes and links not in NewModel.

            // Pull over data form nodes and links from graph
            // and update this.nodes and this.links with it.
            // kinda a duplicate job but hey ho.
            for (var x = 0; x < newTopologyGraphJSON.nodes.length; x++) {
                var xx = newTopologyGraphJSON.nodes[x];
                this.updateNode(this.findNode(xx.data.sysname), xx.data);
            }

            for (var n = 0; n < newTopologyGraphJSON.links.length; n++) {
                var nx = newTopologyGraphJSON.links[n];
                this.updateLink(nx);
            }
            // all updates done, now hopefully self.update() is called! ;-)
        },
        // Private graph functions that works on this.nodes and this.links
        // (this.force algorithm uses this.nodes and this.links)
        addNode: function (id, data) {
            data.id = id;
            this.nodes.push(data);
            //update()
        },
        updateNode: function (node, data) {
            // node must be a node from this.nodes
            node.data = data;
            if (!!node.data.position && !node.isDirty) {
                node.x = node.data.position.x;
                node.y = node.data.position.y;
                node.fixed = true;
            }
        },
        removeNode: function (id) {
            var i = 0;
            var n = this.findNode(id);
            while (i < this.links.length) {
                if ((this.links[i].source === n) || (this.links[i].target) === n) {
                    this.links.splice(i,1); // remove from links if found.
                } else {
                    i++;
                }
            }
            this.nodes.splice(this.findNodeIndex(n.id), 1);
            //update()
        },
        removeLink: function (a, b) {
            var linkIndex = this.findLinkIndex(a, b);
            if (linkIndex) {
                this.links.splice(linkIndex,1);
            }
            /// reassign indexes in this.nodes?
        },
        addLink: function (source, target, data) {
            function copyMeta(forceNode, newNode) {
                if (newNode.x) {
                    forceNode.x = newNode.x;
                }
                if (newNode.y) {
                    forceNode.y = newNode.y;
                }
                forceNode.data = newNode.data;
            }

            function getNode(x) {
                var xNode = null;
                if (_.isObject(x)) {
                    xNode = this.findNode(x.id);
                    if (!xNode) {
                        xNode = x;
                    } else {
                        copyMeta(xNode, x);
                    }
                } else {
                    xNode = this.findNode(x);
                }
                return xNode;
            }

            var sourceNode = getNode.call(this, source);
            var targetNode = getNode.call(this, target);

            this.links.push({
                "source": sourceNode,
                "target": targetNode,
                "data": data, "value": 1});

            //update()
        },
        findNode: function (id) {
            for (var i in this.nodes) {
                if (this.nodes[i].id === id) {
                    return this.nodes[i];
                }
            }
            return null;
        },
        findNodeIndex: function (sysname) {
          for (var i in this.nodes) {
              if (this.nodes[i].id === sysname) {
                  return i;
              }
          }
            return null;
        },
        findLink: function (sourceId, targetId) {

            var linkIndex = this.findLinkIndex(sourceId, targetId);
            if (linkIndex) {
                return this.links[linkIndex];
            }
            return null;
        },
        findLinkIndex: function (sourceId, targetId) {

            for (var i in this.links) {
                if ((this.links[i].source.id === sourceId) && (this.links[i].target.id === targetId)) {
                    return i;
                }
            }
            return null;
        },
        updateLink: function (update) {
            //sourceSysname-targetSysname

            var linkObject = this.findLink(
                (_.isObject(update.source) ? update.source.data.sysname : update.source),
                (_.isObject(update.target) ? update.target.data.sysname : update.target)
            );
            linkObject.data = update.data;
        },

        // Set operations with equality functions
        // todo: probably move into it's own module.
        difference: function (a, b, equality) {
            // Things that are in A and not in B
            // if A = {1, 2, 3, 4} and B = {2, 4, 6, 8}, then A - B = {1, 3}.
            var diff = [];

            /*
             ax = element in a (delta)
             bx = element in b (delta)
             x = list of elements
             b = list of elements
             */


            for (var i = 0; i < a.length; i++) {
                var ax = a[i];

                var isFound = false;
                for (var j = 0; j < b.length; j++) {
                    var bx = b[j];
                    isFound = equality(ax, bx);
                    if (isFound) {
                        // No need to traverse rest of b, if element ax is found in b
                        break;
                    }
                }
                if (!isFound) {
                    // push element from a if not found in list b
                    diff.push(ax);
                }
            }

            return diff;
        },
        intersection: function (a, b, equality) {
            // Things that are in A and in B
            // if A= {1, 2, 3, 4} and B = {2, 4, 5},
            // then A ∩ B = {2, 4}
            var intersection = [];

            /*
             ax = element in a
             bx = element in b
             a = list of elements
             b = list of elements
             */


            var lookupHelper = {};

            for (var i = 0; i < a.length; i++) {
                var ax = a[i];

                for (var j = 0; j < b.length; j++) {
                    var bx = b[j];
                    if (!!!lookupHelper[ax] && !!!lookupHelper[bx]) {
                        // neither element ax or element bx is in lookuphelper
                        // consider if bx should be added to intersection
                        if (equality(ax, bx)) {
                            // lookup helpers, hopefully makes us fast skip
                            // some elements from equality checking
                            lookupHelper[ax] = 1;
                            lookupHelper[bx] = 1;
                            // bx is is in a , storing it in intersection
                            intersection.push(bx);
                        }
                    }


                }
            }
            return intersection;
        },
        bindMapProperties: function () {
            var self = this;
            this.options.mapProperties.bind("change:displayOrphans", this.update, this);
            this.options.mapProperties.get("categories").each(function(category){
                category.bind("change", self.update, self);
            });
            this.options.mapProperties.bind("change:displayOrphans", this.update, this);
            this.options.mapProperties.bind("change:displayTopologyErrors", this.updateRenderTopologyErrors, this);
            this.options.mapProperties.get("position").each(function (position) {
                position.bind("change", self.updateRenderGroupByPosition, self);
            });
        },
        unbindMapProperties: function () {
            this.options.mapProperties.unbind("change");
            this.options.mapProperties.get("categories").each(function(category){
                category.unbind("change");
            });
            this.options.mapProperties.get("position").each(function (position) {
                position.unbind("change");
            });
        },
        setMapPropertyTopology: function (layer) {
            this.model.set({topology: layer});
            this.loadTopologyGraph();
        },
        setMapPropertyPositionFilter: function (positionCollection) {
            this.options.mapProperties.set({'position': positionCollection});
            this.updateRenderGroupByPosition();
        },
        setMapPropertyDisplayTopologyErrors: function (bool) {
            this.options.mapProperties.set({'displayTopologyErrors': bool});
            this.updateRenderTopologyErrors();
        },
        setGraphNodeFixedStatus: function (data) {
            // data should contain a hashmap with 'sysname' and 'fixed'

            for (var i = 0; i < this.nodes.length; i++) {
                var node = this.nodes[i];
                if (node.data.sysname === data.sysname) {
                    node.fixed = data.fixed;
                    break;
                }
            }
            if (!data.fixed) {
                this.force.resume();
            }
        },
        setGraphNodesCollectionFixedStatus: function (boolValue) {
            _.each(this.nodes, function (node) {
                node.fixed = boolValue;
            });

            this.broker.trigger("netmap:nodes:setFixedDone");

            // re-heat force layout only when fixed positions for
            // all nodes get unset.
            if (!boolValue) {
                this.force.resume();
            }
        },
        setUIMouseOver: function (mouseOverModel) {
            this.ui.mouseover[mouseOverModel.get('name')] = mouseOverModel.get('is_selected');
        },
        setUIVLANSelection: function (navVlanID) {
            this.selected_vlan = navVlanID;
            this.updateRenderVLAN(navVlanID);
        },
        isSelectedVlanInList: function (vlansList) {
            var self = this;
            return _.some(vlansList, function (vlan) {
                return self.selected_vlan.navVlanId === vlan.nav_vlan;
            });
        },
        setMapProperty: function (newActiveMapPropertyModel) {
            this.unbindMapProperties();
            this.options.mapProperties = newActiveMapPropertyModel;
            this.bindMapProperties();

            if (this.model.get('viewid') !== this.options.mapProperties.get('viewid')) {
                this.model = new GraphModel({
                    id: this.options.mapProperties.get('viewid', this.options.viewid),
                    topology: this.options.mapProperties.get('topology', 2)
                });
                this.loadTopologyGraph(true);
            }

        },
        nodeDragStart: function (node) {
            this.isDragMoveTriggered = false;
        },
        nodeDragMove: function (node) {
            this.isDragMoveTriggered = true;
            node.px += d3.event.dx;
            node.py += d3.event.dy;
            node.x += d3.event.dx;
            node.y += d3.event.dy;

            this.force.stop();
            node.fixed = true;
            this.tick();
        },
        nodeDragEnd: function (node) {
            this.tick();
            if (this.isDragMoveTriggered) {
                node.isDirty = true;
                this.force.resume();
                this.nodeOnClick(node);
            }
        },
        nodeOnClick: function (node) {
            this.selected_node = node;
            if (this.options.mapProperties.get('position').has_targets()) {
              this.updateRenderGroupByPosition();
            }

            this.unselectVLANSelectionOnConditionsAndRender(node.data.vlans);

            this.broker.trigger("netmap:selectNetbox", {
             'selectedVlan': this.selected_vlan,
             'netbox': node
             });
        },
        linkOnClick: function (link) {
            this.unselectVLANSelectionOnConditionsAndRender(link.data.uplink.vlans);

            this.broker.trigger("netmap:selectLink", {
                'selectedVlan': this.selected_vlan,
                'link': link
            });
        },
        unselectVLANSelectionOnConditionsAndRender: function (vlansList) {
            // Unselect vlan selection if new node/link doesn't contain selected_vlan
            if (this.selected_vlan && !this.isSelectedVlanInList(vlansList)) {
                this.selected_vlan = null;
                this.updateRenderVLAN(this.selected_vlan);
            }
        },
        search: function (query) {
            this.searchQuery = {
                query: query,
                zoomTarget: null
            };
            // find related box
            for (var i = 0; i < this.nodes.length; i++) {
                var node = this.nodes[i];
                if (node.data.sysname.search(query) !== -1) {
                    this.searchQuery.zoomTarget = node;
                    break;
                }
            }
            if (this.searchQuery.zoomTarget) {
                this.trans = [ (-(this.searchQuery.zoomTarget.x * this.scale) + (this.w / 2)), (-(this.searchQuery.zoomTarget.y * this.scale) + (this.h / 2))];
                this.zoom.translate(this.trans);
                this.bounding_box.attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");
            }
        },
        updateRenderVLAN: function (vlan) {
            var self = this;
            self.selected_vlan = vlan;

            var markVlanNodes = self.nodes.filter(function (d) {

                if (d.data.vlans !== undefined && d.data.vlans && self.selected_vlan) {
                    for (var i = 0; i < d.data.vlans.length; i++) {
                        var vlan = d.data.vlans[i];
                        if (vlan.nav_vlan === self.selected_vlan.navVlanId) {
                            return true;
                        }
                    }
                }
                return false;
            });

            var markVlanLinks = self.links.filter(function (d) {
                if (d.data.uplink.vlans !== undefined && d.data.uplink.vlans && self.selected_vlan) {
                    for (var i = 0; i < d.data.uplink.vlans.length; i++) {
                        var vlan = d.data.uplink.vlans[i];
                        if (vlan.nav_vlan === self.selected_vlan.navVlanId) {
                            return true;
                        }
                    }
                }
                return false;
            });

            var nodesInVLAN = self.nodesInVLAN = self.selectedNodeGroupRoot.selectAll("g circle").data(markVlanNodes, function (d) {
                return d.data.sysname;
            });

            var linksInVlan = self.linksInVLAN = self.selectedLinkGroupRoot.selectAll("g line").data(markVlanLinks, function (d) {
                return d.source.id + "-" + d.target.id;
            });



            nodesInVLAN.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_vlan")
                .attr("cx", function (d) {
                    return d.px;
                })
                .attr("cy", function (d) {
                    return d.py;
                })
                .attr("r", 38);
            linksInVlan.enter()
                .append("svg:line")
                .attr("class", "grouped_by_vlan")
                .attr("x1", function (d) { return d.source.x;})
                .attr("y1", function (d) { return d.source.y;})
                .attr("x2", function (d) { return d.target.x;})
                .attr("y2", function (d) { return d.target.y;});
            nodesInVLAN.exit().remove();
            linksInVlan.exit().remove();

        },
        baseScale:      function () {
            var boundingBox = document.getElementById('boundingbox').getBoundingClientRect();

            var baseWidth = (boundingBox.width+40) / this.scale;
            var baseHeight = (boundingBox.height+40) / this.scale;

            var baseScaleWidth = this.w / baseWidth;
            var baseScaleHeight = this.h / baseHeight;

            var requiredScale = 1;
            if (baseScaleWidth < baseScaleHeight) {
                requiredScale = baseScaleWidth;
            } else {
                requiredScale = baseScaleHeight;
            }
            return requiredScale;
        },
        centerGraph: function () {
            var requiredScale = this.baseScale();
            this.scale = requiredScale;
            this.trans = [(-this.w / 2) * (this.scale - 1), (-this.h / 2) * (this.scale - 1)];
            this.zoom.scale(requiredScale);
            this.zoom.translate(this.trans);
            this.bounding_box.attr("transform",
                "translate(" + this.trans + ") scale(" + this.scale + ")");

        },
        validateTranslateScaleValues: function () {
            if (isNaN(this.scale)) {
                this.scale = 0.5;
            }
            if (this.trans.length !== 2 || isNaN(this.trans[0]) || isNaN(this.trans[1])) {
                //console.log("[Netmap][WARNING] Received invalid translate values, centering graph: {0}".format(self.trans));
                this.trans = [(-this.w / 2) * (this.scale - 1), (-this.h / 2) * (this.scale - 1)];
            }
        },
        updateRenderGroupByPosition: function () {
            var self = this;
            var groupBy = [];

            if (!!self.selected_node) {
                if (self.options.mapProperties.get('position').get('room').get('is_selected')) {
                    groupBy = self.nodes.filter(function (d) {
                        return d.data.roomid === self.selected_node.data.roomid;
                    });
                } else if (self.options.mapProperties.get('position').get('location').get('is_selected')) {
                    groupBy = self.nodes.filter(function (d) {
                        return d.data.locationid === self.selected_node.data.locationid;
                    });
                }
            }
            var nodePositionSelection = this.nodePositionSelection = this.selectedNodeGroupRoot.selectAll("circle.grouped_by_room").data(groupBy, function (d)  {
                return d.data.sysname;
            });

            nodePositionSelection.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_room")
                .attr("r", 34);
            nodePositionSelection
                .attr("cx", function (d) { return d.px; })
                .attr("cy", function (d) { return d.py; });
            nodePositionSelection.exit().remove();
        },
        updateRenderTopologyErrors: function () {

            var linksWithErrors = [];

            if (this.options.mapProperties.get('displayTopologyErrors', false)) {
                linksWithErrors = this.links.filter(function (d) {
                    return d.data.tip_inspect_link;
                });
            }

            var linkErrors = this.linkErrors = this.linkErrorsGroupRoot.selectAll("g line").data(linksWithErrors, function (d) {
                    return d.source.id + "-" + d.target.id;
            });

            linkErrors.enter()
                .append("svg:line")
                .attr("class", "warning_inspect");
            linkErrors
                .attr("x1", function (d) {
                    return d.source.x;
                })
                .attr("y1", function (d) {
                    return d.source.y;
                })
                .attr("x2", function (d) {
                    return d.target.x;
                })
                .attr("y2", function (d) {
                    return d.target.y;
                });
            linkErrors.exit()
                .remove();


        },
        updateRenderOrphanFilter: function () {
            var self = this;

            if (!self.options.mapProperties.get('displayOrphans')) {
                for (var i = 0; i < self.nodes.length; i++) {
                    var node = self.nodes[i];

                    var hasNeighbors = false;
                    for (var j = 0; j < self.links.length; j++) {
                        var link = self.links[j];
                        if (link.source === node || link.target === node) {
                            hasNeighbors = true;
                            break;
                        }
                    }

                    if (!hasNeighbors) {
                        self.nodes.splice(i, 1);
                        i--;
                    }
                }
            }

        },
        updateRenderCategories: function () {
            var self = this;

            // selected categories
            var categories = self.options.mapProperties.get('categories').filter(function (category) {
                return category.get('is_selected', false);
            });

            this.updateTopologyGraph(this.model.toJSON());
            // nodes left after filtering out non-selected categories
            var nodesToKeep = _.filter(this.nodes, function (node) {
                return isNodeInCategorySet(node);
            });

            var linksToKeep = _.filter(this.links, function (link) {
               return isNodeInCategorySet(link.source) && isNodeInCategorySet(link.target);
            });


            this.updateTopologyGraph({
                'nodes': nodesToKeep,
                'links': linksToKeep
            });

            function isNodeInCategorySet(node) {
                return _.some(categories, function (category) {
                    return category.get('name').toUpperCase() === (node.data.category + "").toUpperCase();
                });
            }
        },

        updateRenderLinks: function () {
            var self = this;

            var linkGroup = self.linkGroupRoot.selectAll("g.link").data(self.links, function (k) {
                return k.source.id + "-" + k.target.id;
            });

            // Create group element for a link.
            var group = linkGroup.enter()
                .append("svg:g")
                .attr("class", "link");

            var gradient = updateGradient(linkGroup);
            updateStopsInGradient(gradient);
            updateLinkLines(group);

            linkGroup.exit().transition()
                .duration(750)
                .style("fill-opacity", 1e-6).remove();



            // link lines updated for force.tick() movement.
            self.link = linkGroup.selectAll("line");
            self.link
                .on("click", function (d) {
                    self.linkOnClick.call(self, d);
                })
                .on("mouseover", function (d) {
                    if (self.ui.mouseover.links) {
                        self.linkOnClick.call(self, d);
                    }
                });


            // NOTICE: Helper Functions below only.

            // Stops in the gradient to make a nice 0-100% flow on traffic load average
            function updateGradient(linkGroup) {
                var gradient = linkGroup.selectAll(".linkload").data(function (d) {
                    return [d];
                }, function (key) {
                    return key.source.id + "-" + key.target.id;
                });
                gradient.enter()
                    .append("svg:linearGradient")
                    .attr("class", "linkload")
                    .attr("id", function (d) {
                        return "linkload" + d.source.id + "-" + d.target.id;
                    })
                    .attr('x1', '0%')
                    .attr('y1', '0%')
                    .attr('x2', '0%')
                    .attr('y2', '100%');
                gradient.exit().remove();
                return gradient;
            }

            function updateStopsInGradient(gradient) {
                var stops = gradient.selectAll("stop").data(function (d) {
                    return [
                        {percent: 0, css: d.data.traffic.inOctets_css},
                        {percent: 50, css: d.data.traffic.inOctets_css },
                        {percent: 51, css: d.data.traffic.outOctets_css},
                        {percent: 100, css: d.data.traffic.outOctets_css}
                    ];
                });
                stops.enter()
                    .append("svg:stop")
                    .attr("class", "foo")
                    .attr("offset", function (d) {
                        return d.percent + "%";
                    });
                stops.attr("style", function (d) {
                    if (d.css) {
                        return 'stop-color:rgb(' + d.css + '); stop-opacity:1';
                    }
                    else {
                        return 'stop-color:rgb(0,0,0);stop-opacity:1';
                    }
                });
                stops.exit().transition()
                    .duration(750)
                    .style("fill-opacity", 1e-6).remove();
            }

            // Defined link speeds
            //0-100, 100-512,512-2048,2048-4096,>4096 Mbit/s
            function updateLinkLines(group) {
                group
                    .append("svg:line")
                    .attr("class", function (d) {
                        var speed = d.data.link_speed;
                        var classes = "link ";
                        if (speed <= 100) {
                            classes = 'speed0-100';
                        }
                        else if (speed > 100 && speed <= 512) {
                            classes = 'speed100-512';
                        }
                        else if (speed > 512 && speed <= 2048) {
                            classes = 'speed512-2048';
                        }
                        else if (speed > 2048 && speed <= 4096) {
                            classes = 'speed2048-4096';
                        }
                        else if (speed > 4096) {
                            classes = 'speed4096';
                        }
                        else {
                            classes = 'speedunknown';
                        }
                        return classes;
                    })
                    .attr('stroke', function (d) {
                        return 'url(#linkload' + d.source.id + "-" + d.target.id + ')';

                    })
                    .attr("x1", function (d) {
                        return d.source.x;
                    })
                    .attr("y1", function (d) {
                        return d.source.y;
                    })
                    .attr("x2", function (d) {
                        return d.target.x;
                    })
                    .attr("y2", function (d) {
                        return d.target.y;
                    });
            }
        },
        updateRenderNodes: function () {
            var self = this;

            var nodeData = this.node = this.nodeGroupRoot.selectAll("g.node").data(self.nodes, function (d) {
                return d.data.sysname;
            });

            var nodeGroup = nodeData.enter()
                .append("svg:g")
                .attr("class", "node");

            var nodeCategoryImage = nodeGroup.selectAll("image.node").data(function (d) { return [d]; }).enter()
                .append("svg:image")
                .attr("class", "circle node")
                .attr("x", "-16px")
                .attr("y", "-16px")
                .attr("width", "32px")
                .attr("height", "32px");
            nodeCategoryImage
                .attr("xlink:href", function (d) {
                    return self.imagesPrefix + d.data.category.toLowerCase() + ".png";
                });

            var nodeSysname = nodeGroup.selectAll("text.sysname").data(function (d) { return [d]; }).enter()
                .append("svg:text")
                .attr("class", "sysname")
                .attr("dy", "1.5em")
                .attr("class", "node")
                .attr("text-anchor", "middle")
                .attr("fill", "#000000")
                .attr("background", "#c0c0c0");
            nodeSysname.text(function (d) {
                return d.data.sysname;
            });

            var nodeIp = nodeGroup.selectAll("text.ip").data(function (d) { return [d]; }).enter()
                .append("svg:text")
                .attr("class", "ip")
                .attr("dy", "3em")
                .attr("fill", "red");
            nodeIp.text(function (d) {
                return d.data.ip;
            });



            nodeData.exit().transition()
                .duration(750)
                .attr("y", 60)
                .style("fill-opacity", 1e-6)
                .remove();


            var nodeDragAndDrop = d3.behavior.drag()
                .on("dragstart", function (d) { self.nodeDragStart.call(self,d); })
                .on("drag", function (d) { self.nodeDragMove.call(self,d); })
                .on("dragend", function (d) { self.nodeDragEnd.call(self,d); });
            nodeGroup
                .on("click", function (node) {
                    self.nodeOnClick.call(self, node);
                })
                .on("mouseover", function (d) {
                    if (self.ui.mouseover.nodes) {
                        self.nodeOnClick.call(self, d);
                    }
                })
                .call(nodeDragAndDrop);
        },
        update: function () {
            var self = this;

            this.bounding_box
                .attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");

            this.updateRenderTopologyErrors();
            this.updateRenderCategories();
            this.updateRenderOrphanFilter();
            this.updateRenderVLAN();
            this.updateRenderNodes();
            this.updateRenderLinks();
            this.updateRenderGroupByPosition();

            // coordinate helper box
            /*svg
             .append('svg:rect')
             .attr('width', self.w)
             .attr('height', self.h)
             .attr('fill', 'd5d5d5');*/

            this.force.start();
        },
        zoomRescaleFromActiveProperty: function (mapPropertyZoom) {
            var tmp = mapPropertyZoom.split(";");
            this.trans = tmp[0].split(",");
            this.scale = tmp[1];
            this.validateTranslateScaleValues();
            this.zoom.translate(this.trans);
            this.zoom.scale(this.scale);
            this.bounding_box
                .attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");
        },
        zoomRescale: function () {
            this.trans = d3.event.translate;
            this.scale = d3.event.scale;
            this.options.mapProperties.set({
                'zoom': this.trans + ";" + this.scale
            }, {silent: true});
            this.bounding_box.attr("transform",
                "translate(" + this.trans + ") scale(" + this.scale + ")");
        },
        tick: function () {

            this.node.attr("transform", function (d, i) {
                return "translate(" + d.x + "," + d.y + ")";
            });

            this.link
                .attr("x1", function (d) {
                    return d.source.x;
                })
                .attr("y1", function (d) {
                    return d.source.y;
                })
                .attr("x2", function (d) {
                    return d.target.x;
                })
                .attr("y2", function (d) {
                    return d.target.y;
                }
            );


            this.nodePositionSelection
                    .attr("cx", function (d) {
                        return d.px;
                    })
                    .attr("cy", function (d) {
                        return d.py;
                    });

            this.linkErrors
                .attr("x1", function (d) {
                    return d.source.x;
                })
                .attr("y1", function (d) {
                    return d.source.y;
                })
                .attr("x2", function (d) {
                    return d.target.x;
                })
                .attr("y2", function (d) {
                    return d.target.y;
                });

            this.nodesInVLAN
                .attr("cx", function (d) {
                    return d.px;
                })
                .attr("cy", function (d) {
                    return d.py;
                });
            this.linksInVLAN
                .attr("x1", function (d) { return d.source.x;})
                .attr("y1", function (d) { return d.source.y;})
                .attr("x2", function (d) { return d.target.x;})
                .attr("y2", function (d) { return d.target.y;});
        },
        stopLayoutForce: function () {
            this.force.stop();
        },
        render: function () {
            var self = this;

            this.force.on('start', function () {
                self.broker.trigger("netmap:forceRunning", true);
            });

            this.force.on('end', function () {
                self.broker.trigger("netmap:forceRunning", false);
            });
            this.force.on("tick", function () {
                self.tick.apply(self);
            });


            return this;
        },
        resizeAnimate: function (margin) {
            // margin contains either marginLeft or marginRight in it's
            // hashmap with a numeric px value for what to use as a margin
            var self = this;

            var animates = {};
            if (margin.marginLeft) {
                animates['margin-left'] = "{0}px".format(margin.marginLeft);
            }
            if (margin.marginRight) {
                animates['margin-right'] = "{0}px".format(margin.marginRight);
            }

            // parent is $("#netmap_main_view"), required due to 3col collapse
            // layout. This breaks container principle, but it's django
            // who renders backbone.html template.
            this.$el.parent().parent().animate(animates,
                {   duration: 400,
                    step:     function () {
                        self.resize({width: self.$el.innerWidth() - 100});
                    },
                    complete: function () {
                        self.resize({width: self.$el.innerWidth()});
                    }
                });
            //$("#netmap_main_view").animate({'margin-left': "{0}px".format(margin)}, 400);
        },
        resize: function (options) {

            var padding = 93; // make sure it renders in IE by toggling fullscreen and non fullscreen

            if (options && options.width && !isNaN(options.width)) {
                this.w = options.width;
            } else {
                this.w = this.$el.innerWidth();
                var paddingForVerticalScrollbar = (document.body.scrollHeight - document.body.clientHeight);
                if (paddingForVerticalScrollbar > 0 && this.w > paddingForVerticalScrollbar) {
                    this.w -= 10; // scrollbar takes 10px approx.
                }
            }

            this.h = $(window).height();
            if ($("#header").is(':visible')) {
                this.h -= $("#header").height();
            }
            if ($("#footer").is(':visible')) {
                this.h -= $("#footer").height();
                this.h -= $("#debug").height();
            }
            this.h -= padding;

            (this.$el).find('#svg-netmap').attr('width', this.w);
            (this.$el).find('#svg-netmap').attr('height', this.h);
            (this.$el).find('#svg-netmap').attr('style', "width: {0}px; height: {1}px".format(this.w, this.h));
            (this.$el).find('#svg-netmap rect').attr('width', this.w);
            (this.$el).find('#svg-netmap rect').attr('height', this.h);

        },
        close:function () {
            this.force.stop();
            this.broker.unregister(this);
            $(window).off("resize.app");
            this.$el.unbind();
            this.$el.remove();
        }
    });
    return drawNetmapView;
});

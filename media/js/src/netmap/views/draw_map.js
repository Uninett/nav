define([
    'plugins/netmap-extras',
    'plugins/d3force',
    'plugins/set_equality',
    'netmap/resource',
    'netmap/models/graph',
    'netmap/views/loading_spinner',
    // Pull in the Collection module from above
    'libs-amd/text!netmap/templates/draw_map.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapExtras, D3ForceHelper, SetEquality, Resources, GraphModel, LoadingSpinnerView, netmapTemplate) {

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
            this.selectedVLANObject = (!!this.options.nav_vlanid ? this.options.nav_vlanid : null);
            this.ui = {
                'mouseover': {
                    'nodes': false,
                    'links': false
                }
            };


            this.svg = null;
            this.$el.append(netmapTemplate);
            this.spinnerView = new LoadingSpinnerView({el: '#netmap_main_view'});
            this.showLoadingSpinner(true);

            if (!this.options.activeMapModel) {
                this.options.activeMapModel = Resources.getActiveMapModel();
            }

            this.w = this.options.cssWidth;
            this.resize({width: this.w});

            this.force = d3.layout.force().gravity(0.1).charge(-2500).linkDistance(250).size([this.w, this.h]);
            this.nodes = this.force.nodes();
            this.links = this.force.links();
            this.forceHelper = new D3ForceHelper(this.nodes, this.links);

            // swap .on with .bind for jQuery<1.7
            $(window).on("resize.app", _.bind(this.resize, this));

            this.model = new GraphModel({
              id: this.options.activeMapModel.get('viewid', this.options.viewid),
              topology: this.options.activeMapModel.get('topology', 2)
            });

            this.initializeDOM();

            this.loadTopologyGraph();

            this.broker.register(this);
            this.bindActiveMapModel();
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
        showLoadingSpinner: function (boolValue) {
            if (boolValue) {
                (this.$el).find('#svg-netmap').hide();
                this.spinnerView.start();
            } else {
                if (this.spinnerView) {
                    this.spinnerView.stop();
                }
                (this.$el).find('#svg-netmap').show();
            }
        },
        loadTopologyGraph: function (shouldRezoomAndTranslate) {
            // shouldRezoomAndTranslate can be set to true
            // when you want to zoom and translate from activeMapProperties
            // ie: when changing a saved mapProperties view
            // and you want to use it's new saved zoom and translate
            // values from the new activeMapProperties to change the perspective
            var self = this;
            this.showLoadingSpinner(true);
            this.broker.trigger("netmap:graph:isDoneLoading", false);


            this.model.fetch({
                success: function (model) {
                    self.model = model;
                    var newModel = model.toJSON();

                    if (self.isGraphLoadingForFirstTime) {
                        _.each(newModel.nodes, function(nodeObject, i) {
                            self.forceHelper.addNode(nodeObject.data.sysname, nodeObject);
                        });
                        _.each(newModel.links, function (linkObject) {
                            self.forceHelper.addLink(linkObject.source, linkObject.target, linkObject.data);
                        });

                        self.zoomRescaleFromActiveProperty(self.options.activeMapModel.get('zoom'));
                        self.isGraphLoadingForFirstTime = false;
                    } else {
                        self.updateTopologyGraph(newModel);
                    }

                    if (shouldRezoomAndTranslate) {
                        self.zoomRescaleFromActiveProperty(self.options.activeMapModel.get('zoom'));
                    }
                    self.update(); // calls rest of the updateRender functions which updates the SVG.
                    self.broadcastGraphCopy();
                    self.broker.trigger("netmap:graph:isDoneLoading", true);
                    self.showLoadingSpinner(false);
                },
                error: function () {
                    alert("Error loading graph, please try to reload the page");
                    self.broker.trigger("netmap:graph:isDoneLoading", true);
                    self.showLoadingSpinner(false);
                }
            });
        },

        sysnameFromLinkObjectOrGraphModelFetch: function (linkOrGraph) {
            var sourceSysname = (_.isObject(linkOrGraph.source) ? linkOrGraph.source.data.sysname : linkOrGraph);
            var targetSysname = (_.isObject(linkOrGraph.target) ? linkOrGraph.target.data.sysname : linkOrGraph);
            return sourceSysname+"-"+targetSysname;
        },
        updateTopologyGraph: function (newTopologyGraphJSON) {
            var self = this;

            // nodes in this.nodes not present in newTopologyGraphJSON.nodes
            var toRemove = SetEquality.difference(this.nodes, newTopologyGraphJSON.nodes, function (aNode, bNode) {
                return aNode.data.sysname === bNode.data.sysname;
            });

            // nodes present in newTopologyGraphJSON.nodes and not in this.nodes
            var toAdd = SetEquality.difference(newTopologyGraphJSON.nodes, this.nodes, function (aNode, bNode) {
                return aNode.data.sysname === bNode.data.sysname;
            });


            // delete existing nodes not in new model json
            for (var i = 0; i < toRemove.length; i++) {
                var nodeToRemove = toRemove[i];
                this.forceHelper.removeNode(nodeToRemove.data.sysname);
            }

            for (var j = 0; j < toAdd.length; j++) {
                var nodeToAdd = toAdd[j];
                this.forceHelper.addNode(nodeToAdd.data.sysname, nodeToAdd);
            }


            // LINKS handling starts here
            // newTopologyGraphJSOn.links (source and target) is not objects
            // when comming from a GraphModel (model) fetch operation.



            // links to remove that are not present in newTopologyGraphJSON.links, but in this.links
            // (even if removeNode clears links from it, it might be that node is available in this.nodes
            // but should have it links removed...)
            var linksToRemove = SetEquality.difference(this.links, newTopologyGraphJSON.links, function (aLink, bLink) {
                // bLink can be either string or link object.
                return self.sysnameFromLinkObjectOrGraphModelFetch(bLink) === self.sysnameFromLinkObjectOrGraphModelFetch(aLink);
            });

            for (var k = 0; k < linksToRemove.length; k++) {
                var kx = linksToRemove[k];
                this.forceHelper.removeLink(kx.source.data.sysname, kx.target.data.sysname);
            }

            // new links present in newTopologyGraphJSON.links add to this.links
            var linksToAdd = SetEquality.difference(newTopologyGraphJSON.links, this.links, function (aLink, bLink) {
                // aLink can be either string or link object
                return self.sysnameFromLinkObjectOrGraphModelFetch(aLink) === self.sysnameFromLinkObjectOrGraphModelFetch(bLink);
            });

            for (var m = 0; m < linksToAdd.length; m++) {
                var linkToAdd = linksToAdd[m];
                this.forceHelper.addLink(linkToAdd.source, linkToAdd.target, linkToAdd.data);
            }


            // Done adding new nodes and links, and removed non-existing nodes and links not in NewModel.

            // Pull over data form nodes and links from graph
            // and update this.nodes and this.links with it.
            // kinda a duplicate job but hey ho.
            for (var x = 0; x < newTopologyGraphJSON.nodes.length; x++) {
                var nodeToUpdate = newTopologyGraphJSON.nodes[x];
                // findNode used to get the instance already in this.nodes instead of the new one coming from data refresh.
                this.forceHelper.updateNode(self.forceHelper.findNode(nodeToUpdate.data.sysname), nodeToUpdate.data);
            }

            for (var n = 0; n < newTopologyGraphJSON.links.length; n++) {
                var linkToUpdate = newTopologyGraphJSON.links[n];
                this.forceHelper.updateLink(linkToUpdate);
            }
            // all updates done, now hopefully self.update() is called! ;-)
        },
        // Private graph functions that works on this.nodes and this.links
        // (this.force algorithm uses this.nodes and this.links)
        bindActiveMapModel: function () {
            var self = this;
            this.options.activeMapModel.bind("change:displayOrphans", this.update, this);
            this.options.activeMapModel.get("categories").each(function(category){
                category.bind("change", self.update, self);
            });
            this.options.activeMapModel.bind("change:displayOrphans", this.update, this);
            this.options.activeMapModel.bind("change:displayTopologyErrors", this.updateRenderTopologyErrors, this);
            this.options.activeMapModel.get("position").each(function (position) {
                position.bind("change", self.updateRenderGroupByPosition, self);
            });
        },
        unbindActiveMapModel: function () {
            this.options.activeMapModel.unbind("change");
            this.options.activeMapModel.get("categories").each(function(category){
                category.unbind("change");
            });
            this.options.activeMapModel.get("position").each(function (position) {
                position.unbind("change");
            });
        },
        setMapPropertyTopology: function (layer) {
            this.model.set({topology: layer});
            this.loadTopologyGraph();
        },
        setMapPropertyPositionFilter: function (positionCollection) {
            this.options.activeMapModel.set({'position': positionCollection});
            this.updateRenderGroupByPosition();
        },
        setMapPropertyDisplayTopologyErrors: function (boolValue) {
            this.options.activeMapModel.set({'displayTopologyErrors': boolValue});
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

        setUIVLANSelection: function (vlanObject) {
            if (!!vlanObject) {
                if (Backbone.history.getFragment().match(/vlan\/\d+/g)) {
                    Backbone.View.navigate(Backbone.history.getFragment().replace(/vlan\/\d+/g, "vlan/" + vlanObject.navVlanId));
                } else {
                    Backbone.View.navigate(Backbone.history.getFragment() + "/vlan/" + vlanObject.navVlanId);
                }
            }

            this.selectedVLANObject = vlanObject;

            this.updateRenderVLAN(vlanObject);
        },
        isSelectedVlanInList: function (vlansList) {
            var self = this;
            return _.some(vlansList, function (vlan) {
                return self.selectedVLANObject.navVlanId === vlan.nav_vlan;
            });
        },
        setMapProperty: function (newActiveMapPropertyModel) {
            this.unbindActiveMapModel();
            this.options.activeMapModel = newActiveMapPropertyModel;
            this.setUIVLANSelection(null);
            this.bindActiveMapModel();

            if (this.model.get('viewid') !== this.options.activeMapModel.get('viewid')) {
                this.model = new GraphModel({
                    id: this.options.activeMapModel.get('viewid', this.options.viewid),
                    topology: this.options.activeMapModel.get('topology', 2)
                });
                this.loadTopologyGraph(true);
            }

        },
        nodeDragStart: function (nodeObject) {
            this.isDragMoveTriggered = false;
        },
        nodeDragMove: function (nodeObject) {
            this.isDragMoveTriggered = true;
            nodeObject.px += d3.event.dx;
            nodeObject.py += d3.event.dy;
            nodeObject.x += d3.event.dx;
            nodeObject.y += d3.event.dy;

            this.force.stop();
            nodeObject.fixed = true;
            this.tick();
        },
        nodeDragEnd: function (nodeObject) {
            this.tick();
            if (this.isDragMoveTriggered) {
                nodeObject.isDirty = true;
                this.force.resume();
                this.nodeOnClick(nodeObject);
            }
        },
        nodeOnClick: function (nodeObject) {
            this.selected_node = nodeObject;
            if (this.options.activeMapModel.get('position').has_targets()) {
              this.updateRenderGroupByPosition();
            }

            this.unselectVLANSelectionOnConditionsAndRender(nodeObject.data.vlans);

            this.broker.trigger("netmap:selectNetbox", {
             'selectedVlan': this.selectedVLANObject,
             'netbox': nodeObject
             });
        },
        linkOnClick: function (linkObject) {
            this.unselectVLANSelectionOnConditionsAndRender(linkObject.data.uplink.vlans);

            this.broker.trigger("netmap:selectLink", {
                'selectedVlan': this.selectedVLANObject,
                'link': linkObject
            });
        },
        unselectVLANSelectionOnConditionsAndRender: function (vlansList) {
            // Unselect vlan selection if new node/link doesn't contain selected_vlan
            if (this.selectedVLANObject && !this.isSelectedVlanInList(vlansList)) {
                this.selectedVLANObject = null;
                Backbone.View.navigate(Backbone.history.stripTrailingSlash(Backbone.history.getFragment().replace(/vlan\/\d+/g, "")));
                this.updateRenderVLAN(this.selectedVLANObject);
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
        updateRenderVLAN: function (vlanObject) {
            var self = this;
            self.selectedVLANObject = vlanObject;

            var markVlanNodes = self.nodes.filter(function (nodeObject) {

                if (nodeObject.data.vlans !== undefined && nodeObject.data.vlans && self.selectedVLANObject) {
                    for (var i = 0; i < nodeObject.data.vlans.length; i++) {
                        var vlan = nodeObject.data.vlans[i];
                        if (vlan.nav_vlan === self.selectedVLANObject.navVlanId) {
                            return true;
                        }
                    }
                }
                return false;
            });

            var markVlanLinks = self.links.filter(function (linkObject) {
                if (linkObject.data.uplink.vlans !== undefined && linkObject.data.uplink.vlans && self.selectedVLANObject) {
                    for (var i = 0; i < linkObject.data.uplink.vlans.length; i++) {
                        var vlan = linkObject.data.uplink.vlans[i];
                        if (vlan.nav_vlan === self.selectedVLANObject.navVlanId) {
                            return true;
                        }
                    }
                }
                return false;
            });

            var nodesInVLAN = self.nodesInVLAN = self.selectedNodeGroupRoot.selectAll("g circle").data(markVlanNodes, function (nodeObject) {
                return nodeObject.data.sysname;
            });

            var linksInVlan = self.linksInVLAN = self.selectedLinkGroupRoot.selectAll("g line").data(markVlanLinks, function (linkObject) {
                return linkObject.source.id + "-" + linkObject.target.id;
            });


            nodesInVLAN.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_vlan")
                .attr("cx", function (nodeObject) {
                    return nodeObject.px;
                })
                .attr("cy", function (nodeObject) {
                    return nodeObject.py;
                })
                .attr("r", 38);
            linksInVlan.enter()
                .append("svg:line")
                .attr("class", "grouped_by_vlan")
                .attr("x1", function (linkObject) { return linkObject.source.x;})
                .attr("y1", function (linkObject) { return linkObject.source.y;})
                .attr("x2", function (linkObject) { return linkObject.target.x;})
                .attr("y2", function (linkObject) { return linkObject.target.y;});
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
                if (self.options.activeMapModel.get('position').get('room').get('is_selected')) {
                    groupBy = self.nodes.filter(function (nodeObject) {
                        return nodeObject.data.roomid === self.selected_node.data.roomid;
                    });
                } else if (self.options.activeMapModel.get('position').get('location').get('is_selected')) {
                    groupBy = self.nodes.filter(function (nodeObject) {
                        return nodeObject.data.locationid === self.selected_node.data.locationid;
                    });
                }
            }
            var nodePositionSelection = this.nodePositionSelection = this.selectedNodeGroupRoot.selectAll("circle.grouped_by_room").data(groupBy, function (nodeObject)  {
                return nodeObject.data.sysname;
            });

            nodePositionSelection.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_room")
                .attr("r", 34);
            nodePositionSelection
                .attr("cx", function (nodeObject) { return nodeObject.px; })
                .attr("cy", function (nodeObject) { return nodeObject.py; });
            nodePositionSelection.exit().remove();
        },
        updateRenderTopologyErrors: function () {

            var linksWithErrors = [];

            if (this.options.activeMapModel.get('displayTopologyErrors', false)) {
                linksWithErrors = this.links.filter(function (linkObject) {
                    return linkObject.data.tip_inspect_link;
                });
            }

            var linkErrors = this.linkErrors = this.linkErrorsGroupRoot.selectAll("g line").data(linksWithErrors, function (linkObject) {
                    return linkObject.source.id + "-" + linkObject.target.id;
            });

            linkErrors.enter()
                .append("svg:line")
                .attr("class", "warning_inspect");
            linkErrors
                .attr("x1", function (linkObject) {
                    return linkObject.source.x;
                })
                .attr("y1", function (linkObject) {
                    return linkObject.source.y;
                })
                .attr("x2", function (linkObject) {
                    return linkObject.target.x;
                })
                .attr("y2", function (linkObject) {
                    return linkObject.target.y;
                });
            linkErrors.exit()
                .remove();


        },
        updateRenderOrphanFilter: function () {
            // actually doesn't render anything,
            // it's removing links and nodes after other
            // updateRender* functions that modify this.links and this.nodes!
            var self = this;

            if (!self.options.activeMapModel.get('displayOrphans')) {
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
            var categories = self.options.activeMapModel.get('categories').filter(function (category) {
                return category.get('is_selected', false);
            });

            this.updateTopologyGraph(this.model.toJSON());
            // nodes left after filtering out non-selected categories
            var nodesToKeep = _.filter(this.nodes, function (nodeObject) {
                return isNodeInCategorySet(nodeObject);
            });

            var linksToKeep = _.filter(this.links, function (linkObject) {
               return isNodeInCategorySet(linkObject.source) && isNodeInCategorySet(linkObject.target);
            });


            this.updateTopologyGraph({
                'nodes': nodesToKeep,
                'links': linksToKeep
            });

            function isNodeInCategorySet(nodeObject) {
                return _.some(categories, function (categoryAsCheckRadioModel) {
                    return categoryAsCheckRadioModel.get('name').toUpperCase() === (nodeObject.data.category + "").toUpperCase();
                });
            }
        },

        updateRenderLinks: function () {
            var self = this;

            var linkGroup = self.linkGroupRoot.selectAll("g.link").data(self.links, function (linkObject) {
                return linkObject.source.id + "-" + linkObject.target.id;
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
                .on("click", function (linkObject) {
                    self.linkOnClick.call(self, linkObject);
                })
                .on("mouseover", function (linkObject) {
                    if (self.ui.mouseover.links) {
                        self.linkOnClick.call(self, linkObject);
                    }
                });


            // NOTICE: Helper Functions below only.

            // Stops in the gradient to make a nice 0-100% flow on traffic load average
            function updateGradient(linkGroup) {
                var gradient = linkGroup.selectAll(".linkload").data(function (linkObject) {
                    return [linkObject];
                }, function (linkObject) {
                    return linkObject.source.id + "-" + linkObject.target.id;
                });
                gradient.enter()
                    .append("svg:linearGradient")
                    .attr("class", "linkload")
                    .attr("id", function (linkObject) {
                        return "linkload" + linkObject.source.id + "-" + linkObject.target.id;
                    })
                    .attr('x1', '0%')
                    .attr('y1', '0%')
                    .attr('x2', '0%')
                    .attr('y2', '100%');
                gradient.exit().remove();
                return gradient;
            }

            function updateStopsInGradient(gradient) {
                var stops = gradient.selectAll("stop").data(function (linkObject) {
                    return [
                        {percent: 0, css: linkObject.data.traffic.inOctets_css},
                        {percent: 50, css: linkObject.data.traffic.inOctets_css },
                        {percent: 51, css: linkObject.data.traffic.outOctets_css},
                        {percent: 100, css: linkObject.data.traffic.outOctets_css}
                    ];
                });
                stops.enter()
                    .append("svg:stop")
                    .attr("class", "foo")
                    .attr("offset", function (gradientData) {
                        return gradientData.percent + "%";
                    });
                stops.attr("style", function (gradientData) {
                    if (gradientData.css) {
                        return 'stop-color:rgb(' + gradientData.css + '); stop-opacity:1';
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
                    .attr("class", function (linkObject) {
                        var speed = linkObject.data.link_speed;
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
                    .attr('stroke', function (linkObject) {
                        return 'url(#linkload' + linkObject.source.id + "-" + linkObject.target.id + ')';

                    })
                    .attr("x1", function (linkObject) {
                        return linkObject.source.x;
                    })
                    .attr("y1", function (linkObject) {
                        return linkObject.source.y;
                    })
                    .attr("x2", function (linkObject) {
                        return linkObject.target.x;
                    })
                    .attr("y2", function (linkObject) {
                        return linkObject.target.y;
                    });
            }
        },
        updateRenderNodes: function () {
            var self = this;

            var nodeData = this.node = this.nodeGroupRoot.selectAll("g.node").data(self.nodes, function (nodeObject) {
                return nodeObject.data.sysname;
            });

            var nodeGroup = nodeData.enter()
                .append("svg:g")
                .attr("class", "node");

            var nodeCategoryImage = nodeGroup.selectAll("image.node").data(function (nodeObject) { return [nodeObject]; }).enter()
                .append("svg:image")
                .attr("class", "circle node")
                .attr("x", "-16px")
                .attr("y", "-16px")
                .attr("width", "32px")
                .attr("height", "32px");
            nodeCategoryImage
                .attr("xlink:href", function (nodeObject) {
                    return self.imagesPrefix + nodeObject.data.category.toLowerCase() + ".png";
                });

            var nodeSysname = nodeGroup.selectAll("text.sysname").data(function (nodeObject) { return [nodeObject]; }).enter()
                .append("svg:text")
                .attr("class", "sysname")
                .attr("dy", "1.5em")
                .attr("class", "node")
                .attr("text-anchor", "middle")
                .attr("fill", "#000000")
                .attr("background", "#c0c0c0");
            nodeSysname.text(function (nodeObject) {
                return nodeObject.data.sysname;
            });

            var nodeIp = nodeGroup.selectAll("text.ip").data(function (nodeObject) { return [nodeObject]; }).enter()
                .append("svg:text")
                .attr("class", "ip")
                .attr("dy", "3em")
                .attr("fill", "red");
            nodeIp.text(function (nodeObject) {
                return nodeObject.data.ip;
            });



            nodeData.exit().transition()
                .duration(750)
                .attr("y", 60)
                .style("fill-opacity", 1e-6)
                .remove();


            var nodeDragAndDrop = d3.behavior.drag()
                .on("dragstart", function (nodeObject) { self.nodeDragStart.call(self, nodeObject); })
                .on("drag", function (nodeObject) { self.nodeDragMove.call(self, nodeObject); })
                .on("dragend", function (nodeObject) { self.nodeDragEnd.call(self, nodeObject); });
            nodeGroup
                .on("click", function (nodeObject) {
                    self.nodeOnClick.call(self, nodeObject);
                })
                .on("mouseover", function (nodeObject) {
                    if (self.ui.mouseover.nodes) {
                        self.nodeOnClick.call(self, nodeObject);
                    }
                })
                .call(nodeDragAndDrop);
        },
        update: function () {
            this.bounding_box
                .attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");

            this.updateRenderTopologyErrors();
            this.updateRenderCategories();
            this.updateRenderOrphanFilter();
            this.updateRenderVLAN(this.selectedVLANObject);
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
            this.options.activeMapModel.set({
                'zoom': this.trans + ";" + this.scale
            }, {silent: true});
            this.bounding_box.attr("transform",
                "translate(" + this.trans + ") scale(" + this.scale + ")");
        },
        tick: function () {

            this.node.attr("transform", function (nodeObject, i) {
                return "translate(" + nodeObject.x + "," + nodeObject.y + ")";
            });

            this.link
                .attr("x1", function (linkObject) {
                    return linkObject.source.x;
                })
                .attr("y1", function (linkObject) {
                    return linkObject.source.y;
                })
                .attr("x2", function (linkObject) {
                    return linkObject.target.x;
                })
                .attr("y2", function (linkObject) {
                    return linkObject.target.y;
                }
            );


            this.nodePositionSelection
                    .attr("cx", function (nodeObject) {
                        return nodeObject.px;
                    })
                    .attr("cy", function (nodeObject) {
                        return nodeObject.py;
                    });

            this.linkErrors
                .attr("x1", function (linkObject) {
                    return linkObject.source.x;
                })
                .attr("y1", function (linkObject) {
                    return linkObject.source.y;
                })
                .attr("x2", function (linkObject) {
                    return linkObject.target.x;
                })
                .attr("y2", function (linkObject) {
                    return linkObject.target.y;
                });

            this.nodesInVLAN
                .attr("cx", function (nodeObject) {
                    return nodeObject.px;
                })
                .attr("cy", function (nodeObject) {
                    return nodeObject.py;
                });
            this.linksInVLAN
                .attr("x1", function (linkObject) { return linkObject.source.x;})
                .attr("y1", function (linkObject) { return linkObject.source.y;})
                .attr("x2", function (linkObject) { return linkObject.target.x;})
                .attr("y2", function (linkObject) { return linkObject.target.y;});
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

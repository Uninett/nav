define([
    'plugins/netmap-extras',
    'netmap/resource',
    'netmap/models/graph',
    'netmap/models/map',
    'netmap/models/default_map',
    'netmap/views/loading_spinner',
    // Pull in the Collection module from above
    'netmap/views/netbox_info',
    'libs-amd/text!netmap/templates/draw_map.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapExtras, Resources, GraphModel, MapModel, DefaultMapModel, LoadingSpinnerView, NetboxInfoView, netmapTemplate) {

    var drawNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "chart",

        broker: Backbone.EventBroker,
        interests: {
            'map:resize:animate': 'resizeAnimate',
            'map:redraw': 'requestRedraw',
            'map:search': 'search',
            'map:centerGraph': 'centerGraph',
            'map:freezeNodes': 'freezeNodes',
            'netmap:selectVlan': 'showVlan',
            'map:ui:mouseover:nodes': 'toggleUIMouseoverNodes',
            'map:ui:mouseover:links': 'toggleUIMouseoverLinks',
            'map:loading:context_selected_map': 'clear',
            'map:node:fixed': 'updateNodeFixedStatus',
            'map:fixNodes': 'updateAllNodePositions',
            'netmap:request:graph': 'broadcastGraph',
            'netmap:changeMapProperties': 'setMapProperties',
            'netmap:changeTopology': 'setMapPropertyLayer',
            'netmap:changeCategoriesFilters': 'setMapPropertyCategories',
            'netmap:changeOrphansFilters': 'setMapPropertyOrphanFilter',
            'netmap:changePositionFilter': 'setMapPropertyPositionFilter',
            'netmap:changeDisplayTopologyErrors': 'setMapPropertyDisplayTopologyErrors',
            'headerFooterMinimize:trigger': 'resize'
        },
        initialize: function () {
            this.broker.register(this);

            this.$el.append(netmapTemplate);
            this.showLoadingSpinner(true);
            this.selected_node = null;
            this.selected_vlan = null;
            this.ui = {
                'topologyErrors': false,
                'mouseover': {
                    'nodes': false,
                    'links': false
                }
            };

            if (!this.options.mapProperties) {
                this.options.mapProperties = Resources.getMapProperties();
            }
            this.sidebar = this.options.view_map_info;

            this.w = this.options.cssWidth;
            this.resize({width: this.w});
            this.force = d3.layout.force()
                .gravity(0.5)
                .distance(2000)
                .charge(-100)
                .size([this.w, this.h]);

            this.trans = [0,0];
            this.scale = 1;
            this.zoom = d3.behavior.zoom();
            // swap .on with .bind for jQuery<1.7
            $(window).on("resize.app", _.bind(this.resize, this));

            //this.model = this.options.context_selected_map.graph;
            //context_selected_map.graph = new GraphModel({id: context_selected_map.id, topology: context_selected_map.map.attributes.topology});
            var self = this;

            this.model = new GraphModel({
              viewid: this.options.mapProperties.get('viewid', this.options.viewid),
              topology: this.options.mapProperties.get('topology', 2)
            });
            self.loadGraph();

        },
        broadcastGraph: function () {
            this.broker.trigger("netmap:graph", this.model);
        },
        showLoadingSpinner: function (bool) {
            if (bool) {
                (this.$el).find('#svg-netmap').hide();

                this.spinnerView = new LoadingSpinnerView();
                this.$el.prepend(this.spinnerView.render().el);
                //debugger;
            } else {
                if (this.spinnerView) {
                    this.spinnerView.close();
                    $(this.svg).show();
                }
            }
        },
        loadGraph: function () {
            var self = this;
            this.model.fetch({
               success: function (model, attributes) {
                   self.model = model;
                   self.postInitialize();
                   self.broker.trigger("netmap:graph", model);
               },
               error: function () {
                    alert("Error loading graph, please try to reload the page");
               }
            });
        },
        postInitialize: function () {
            this.clear();

            if (this.options.mapProperties && !this.options.mapProperties.isNew() && this.options.mapProperties.attributes.zoom !== undefined) {
                var tmp = this.options.mapProperties.get('zoom').split(";");
                this.trans = tmp[0].split(",");
                this.scale = tmp[1];
                this.validateTranslateScaleValues();
                this.zoom.translate(this.trans);
                this.zoom.scale(this.scale);

                this.svg.attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");

            } else {
                // adjust scale and translated according to how many nodes
                // we're trying to draw

                // Guess a good estimated scaling factor
                // (can't use self.baseScale , since svg is not drawn yet)
                //this.scale = 1 / Math.log(nodesCount);
                this.scale = 0.5;

                // translate ( -centerX*(factor-1) , -centerY*(factor-1) ) scale(factor)
                // Example: SVG view pot 800x600, center is 400,300
                // Reduce 30%, translate( -400*(0.7-1), -300*(0.7-1) ) scale(0.7)
                this.trans = [(-this.w / 2) * (this.scale - 1), (-this.h / 2) * (this.scale - 1)];

                this.validateTranslateScaleValues();
                this.zoom.scale(this.scale);
                this.zoom.translate(this.trans);


            }
            this.bindMapProperties();
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);

            this.render();
            this.broker.trigger("netmap:setMapProperties:done", this.options.mapProperties);
            this.showLoadingSpinner(false);
        },
        bindMapProperties: function () {
            this.options.mapProperties.bind("change:topology", this.render, this);
            this.options.mapProperties.bind("change:displayOrphans", this.updateRenderCategories, this);
        },
        setMapProperties: function (mapPropertiesModel) {
            this.showLoadingSpinner(true);
            var self = this;
            var currentViewId = (this.options.mapProperties && this.options.mapProperties.get("viewid"));
            this.options.mapProperties = mapPropertiesModel;
            if (currentViewId !== mapPropertiesModel.get("viewid")) {
                this.options.mapProperties.fetch({success: function (model) {
                    self.options.mapProperties.off("change");
                    self.options.mapProperties = model;
                    self.bindMapProperties();
                    self.model = new GraphModel({viewid: mapPropertiesModel.get("viewid"), topology: mapPropertiesModel.get('topology')});
                    self.loadGraph();
                }});

            } else {
                this.clear();
                this.render();
                this.showLoadingSpinner(false);
            }
            this.bindMapProperties();
            // tell list_maps we're done updating our mapProperties
            // and loaded _graph_ :-)
            this.broker.trigger("netmap:setMapProperties:done", this.options.mapProperties);

        },
        setMapPropertyLayer: function (layer) {
            var self = this;
            self.showLoadingSpinner(true);
            this.model.set({topology: layer});
            this.model.fetch({
                success: function (model, attributes) {
                    self.model = model;
                    self.modelJson = self.model.toJSON();
                    self.clear();
                    self.render();
                    self.showLoadingSpinner(false);
                }
            });
        },
        setMapPropertyCategories: function (categoriesCollection) {
            this.options.mapProperties.set({categories: categoriesCollection});
            this.updateRenderCategories();
        },
        setMapPropertyPositionFilter: function (positionCollection) {
            this.options.mapProperties.set({'position': positionCollection});
            this.updateRenderGroupByPosition();
        },
        setMapPropertyDisplayTopologyErrors: function (bool) {
            this.options.mapProperties.set({'displayTopologyErrors': bool});
            this.updateRenderTopologyErrors();
        },
        resizeAnimate: function (margin) {
            var self = this;

            var marginRight = margin.marginRight;
            var marginLeft = margin.marginLeft;

            // parent is $("#netmap_main_view"), required due to 3col collapse
            // layout. This breaks container principle, but it's django
            // who renders backbone.html template.
            this.$el.parent().parent().animate({
                    'margin-right': "{0}px".format(marginRight),
                    'margin-left':  "{0}px".format(marginLeft)
                },
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
        search: function (query) {
            this.searchQuery = {
                query: query,
                zoomTarget: null
            };
            // find related box
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                if (node.data.sysname.search(query) !== -1) {
                    this.searchQuery.zoomTarget = node;
                    break;
                }
            }
            if (this.searchQuery.zoomTarget) {
                this.trans = [ (-(this.searchQuery.zoomTarget.x * this.scale) + (this.w / 2)), (-(this.searchQuery.zoomTarget.y * this.scale) + (this.h / 2))];
                this.zoom.translate(this.trans);
                this.svg.attr("transform",
                    "translate(" + this.trans + ") scale(" + this.scale + ")");
            }
        },
        showVlan: function (vlan) {
            var self = this;
            self.selected_vlan = vlan;

            if (!self.selected_vlan) {
                self.nodesInVlan.exit().remove();
                self.linksInVlan.exit().remove();
            }

            var markVlanNodes = self.modelJson.nodes.filter(function (d) {

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

            var markVlanLinks = self.modelJson.links.filter(function (d) {
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

            self.nodesInVlan = self.selectedNodeGroup.selectAll("g circle").data(markVlanNodes, function (d) {
                return d.data.sysname;
            });

            self.linksInVlan = self.selectedLinkGroup.selectAll("g line").data(markVlanLinks, function (d) {
                return d.source.id + "-" + d.target.id;
            });



            self.nodesInVlan.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_vlan")
                .attr("cx", function (d) {
                    return d.px;
                })
                .attr("cy", function (d) {
                    return d.py;
                })
                .attr("r", 38);
            self.linksInVlan.enter()
                .append("svg:line")
                .attr("class", "grouped_by_vlan")
                .attr("x1", function (d) { return d.source.x;})
                .attr("y1", function (d) { return d.source.y;})
                .attr("x2", function (d) { return d.target.x;})
                .attr("y2", function (d) { return d.target.y;});
            self.nodesInVlan.exit().remove();
            self.linksInVlan.exit().remove();

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
            this.svg.attr("transform",
                "translate(" + this.trans + ") scale(" + this.scale + ")");

        },
        freezeNodes: function (isFreezing) {
            if (isFreezing) {
                this.force.stop();
            } else {
                this.force.resume();
            }
        },
        toggleUIMouseoverNodes: function (boolean) {
            this.ui.mouseover.nodes = boolean;
        },
        toggleUIMouseoverLinks: function (boolean) {
            this.ui.mouseover.links = boolean;
        },
        clear: function () {
            this.force.stop();
            (this.$el).find('#svg-netmap').remove();
            var self = this;

            this.root_chart = d3.select(this.el)
                .append("svg:svg")
                .attr('id', 'svg-netmap')
                .attr("width", self.w).attr("height", self.h)
                .attr("pointer-events", "all")
                .attr("overflow", "hidden");
            this.root_chart
                .append('svg:rect')
                .attr('width', self.w)
                .attr('height', self.h)
                .attr('fill', 'white')
                .call(self.zoom.on("zoom", redraw));
            this.svg = this.root_chart.append('svg:g')
                .append('svg:g')
                .attr('id', 'boundingbox')
            ;
            this.linkGroupMeta = this.svg.append("svg:g").attr("class", "linksmeta");
            this.selectedNodeGroup = this.svg.append("svg:g").attr("class", "selected_nodes");
            this.selectedLinkGroup = this.svg.append("svg:g").attr("class", "selected_links");
            this.linkGroup = this.svg.append("svg:g").attr("class", "links");
            this.nodeGroup = this.svg.append("svg:g").attr("class", "nodes");

            function redraw() {
                self.trans = d3.event.translate;
                self.scale = d3.event.scale;
                self.options.mapProperties.set({
                    'zoom': self.trans + ";" + self.scale
                }, {silent: true});
                self.svg.attr("transform",
                    "translate(" + self.trans + ") scale(" + self.scale + ")");
            }
        },
        updateNodeFixedStatus: function (data) {
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                if (node.data.sysname === data.sysname) {
                    node.fixed = data.fixed;
                    break;
                }
            }
            if (!data.fixed) {
                this.force.resume();
            }
        },
        updateAllNodePositions: function (boolean) {
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                node.fixed = boolean;
            }
            this.sidebar.render();
            if (!boolean) {
                this.force.resume();
            }
        },
        requestRedraw: function (options) {
            this.clear();
            this.render();
        },
        validateTranslateScaleValues: function () {
            if (isNaN(this.scale)) {
                this.scale = this.baseScale();
            }
            if (this.trans.length !== 2 || isNaN(this.trans[0]) || isNaN(this.trans[1])) {
                //console.log("[Netmap][WARNING] Received invalid translate values, centering graph: {0}".format(self.trans));
                this.trans = [(-this.w / 2) * (this.scale - 1), (-this.h / 2) * (this.scale - 1)];
            }
        },
        updateRenderCategories: function () {
            function filterNodes(json, selected_categories) {
                var result = [];
                for (var i = 0; i < json.nodes.length; i++) {
                    var node = json.nodes[i];
                    if (node !== null) {
                        if (node.data.position) {
                            node.x = node.data.position.x;
                            node.y = node.data.position.y;
                            node.fixed = true;
                        }
                        var selected_category = selected_categories.get(node.data.category.toUpperCase());
                        if (selected_category && selected_category.get('is_selected')) {
                            result.push(node);
                        } else if (!node.fixed) {
                            // reset it's coordinates if position is not fixed
                            // and it doesn't match filter.

                            /*node.x = 0;
                             node.y = 0;*/

                        }
                    }
                }
                return result;
            }

            function categoryLinksFilter(data, filter_nodes, selected_categories) {
                var json = data;

                var filter_links = [];
                var filter_nodes_indexes = filter_nodes;

                function filterLinks() {
                    var result = [];

                    function isMatchingCriteria() {
                        var sourceMatch = false;
                        var targetMatch = false;
                        var source, target;
                        source = link.source;
                        target = link.target;

                        _.each(selected_categories.models, function (model) {
                            if (source.data.category.toUpperCase() === model.get('name').toUpperCase() &&
                                model.get('is_selected')) {
                                sourceMatch = true;
                            }
                            if (target.data.category.toUpperCase() === model.get('name').toUpperCase() &&
                                model.get('is_selected')) {
                                targetMatch = true;
                            }
                        });
                        return sourceMatch && targetMatch;

                    }

                    for (var x = 0; x < filter_nodes_indexes.length; x++) {
                        var node = filter_nodes_indexes[x];
                        for (var i = 0; i < json.links.length; i++) {
                            var link = json.links[i];
                            var source, target;
                            source = link.source;
                            target = link.target;

                            if (target === node) {
                                if (isMatchingCriteria(link)) {
                                    result.push(link);
                                }
                            }
                        }

                    }
                    return result;
                }

                filter_links = filterLinks();

                return filter_links;
            }


            var self = this;
            self.modelJson = self.model.toJSON();
            self.force.nodes(self.modelJson.nodes).links(self.modelJson.links);
            // Category filter, finds nodes to keep, filters em out and
            // remaps links
            var keepNodes = filterNodes(self.modelJson, self.options.mapProperties.get('categories'));
            self.modelJson.nodes = self.intersectionObjects(
                self.modelJson.nodes,
                keepNodes,
                function (a, b) {
                    return a.data.sysname === b.data.sysname;
                });
            self.modelJson.links = categoryLinksFilter(self.modelJson, keepNodes, self.options.mapProperties.get('categories'));

            var linkedByIndex = {};
            self.modelJson.links.forEach(function (d) {
                linkedByIndex[d.source.data.sysname + "," + d.target.data.sysname] = 1;
            });
            self.updateRenderOrphanFilter();
            self.draw(self.modelJson);
            self.force.start();

            //self.updateRenderLinks();
            //self.updateRenderNodes();
        },
        updateRenderGroupByPosition: function () {
            var self = this;
            var groupBy = null;

            if (self.options.mapProperties.get('position').get('room').get('is_selected')) {
                groupBy = self.modelJson.nodes.filter(function (d) {
                    if (!self.selected_node) { return false; }
                    return d.data.roomid === self.selected_node.data.roomid;
                });
            } else if (self.options.mapProperties.get('position').get('location').get('is_selected')) {
                groupBy = self.modelJson.nodes.filter(function (d) {
                    if (!self.selected_node) { return false; }
                    return d.data.locationid === self.selected_node.data.locationid;
                });
            } else {
                groupBy = [];
            }

            self.nodesInRoom = self.svg.selectAll("g circle").data(groupBy, function (d) {
                return d.data.sysname;
            });

            self.nodesInRoom.enter()
                .append("svg:circle")
                .attr("class", "grouped_by_room")
                .attr("cx", function (d) {
                    return d.px;
                })
                .attr("cy", function (d) {
                    return d.py;
                })
                .attr("r", 34);
            self.nodesInRoom.exit().remove();
        },
        updateRenderTopologyErrors: function () {
            var self = this;
            if (self.linkErrors !== undefined && !self.options.mapProperties.displayTopologyErrors) {
                self.linkErrors.exit().remove();
            } else if (self.options.mapProperties.displayTopologyErrors) {

                var linksWithErrors = self.modelJson.links.filter(function (d) {
                    return d.data.tip_inspect_link;
                });

                self.linkErrors = self.linkGroupMeta.selectAll("g line").data(linksWithErrors, function (d) {
                    return d.source.id + "-" + d.target.id;
                });

                self.linkErrors.enter().append("svg:line").attr("class", "warning_inspect");
                self.linkErrors.exit().remove();
            }
        },
        // http://stackoverflow.com/a/8683287/653233
        // intersectionObjects() for the intersection of objects
        // using your equality function of choice
        intersectionObjects: function () {
            function intersectionObjects2 (a, b, areEqualFunction)  {
                var Result = [];

                for(var i = 0; i < a.length; i++) {
                    var aElement = a[i];
                    var existsInB = _.any(b, function(bElement) { return areEqualFunction(bElement, aElement); });
                    if(existsInB) {
                        Result.push(aElement);
                    }
                }

                return Result;
            }
            var Results = arguments[0];
            var LastArgument = arguments[arguments.length - 1];
            var ArrayCount = arguments.length;
            var areEqualFunction = _.isEqual;

            if(typeof LastArgument === "function") {
                areEqualFunction = LastArgument;
                ArrayCount--;
            }

            for(var i = 1; i < ArrayCount ; i++) {
                var array = arguments[i];
                Results = intersectionObjects2(Results, array, areEqualFunction);
                if(Results.length === 0) break;
            }
            return Results;
        },
        updateRenderVLAN: function (vlans) {
            var self = this;
            var foundVlan = false;
            if (vlans !== undefined && vlans) {
                for (var i = 0; i < vlans.length; i++) {
                    var vlan = vlans[i];
                    if (self.selected_vlan.navVlanId === vlan.nav_vlan) {
                        foundVlan = true;
                        break;
                    }
                }
            }
            if (!foundVlan) {
                self.selected_vlan = null;
                self.showVlan(self.selected_vlan);
            }

        },
        updateRenderOrphanFilter: function (requireCategoriesUpdate) {
            var self = this;
            console.log(self.options.mapProperties.get('displayOrphans'));
            if (!self.options.mapProperties.get('displayOrphans')) {
                for (var i = 0; i < self.modelJson.nodes.length; i++) {
                    var node = self.modelJson.nodes[i];

                    var hasNeighbors = false;
                    for (var j = 0; j < self.modelJson.links.length; j++) {
                        var link = self.modelJson.links[j];
                        if (link.source === node || link.target === node) {
                            hasNeighbors = true;
                            break;
                        }
                    }

                    if (!hasNeighbors) {
                        self.modelJson.nodes.splice(i, 1);
                        i--;
                    }
                }

            } else if (requireCategoriesUpdate) {
                self.updateRenderCategories();
            }
            self.draw(self.modelJson);
        },
        updateRenderLinks: function () {
            var self = this;
            //0-100, 100-512,512-2048,2048-4096,>4096 Mbit/s
            self.s_link = self.linkGroup.selectAll("g line").data(self.modelJson.links, function (d) {
                return d.source.id + "-" + d.target.id;
            });

            self.s_link.enter().append("svg:g").attr("class", "link").forEach(function (d, i) {
                var gradient = self.s_link
                    .append("svg:linearGradient")
                    .attr("id", function (d, i) {
                        return 'linkload' + i;
                    })
                    .attr('x1', '0%')
                    .attr('y1', '0%')
                    .attr('x2', '0%')
                    .attr('y2', '100%');
                gradient
                    .append("svg:stop")
                    .attr('offset', '0%')
                    .attr('style', function (d) {
                        if (d.data.traffic.inOctets_css) { return 'stop-color:rgb(' + d.data.traffic.inOctets_css + ');stop-opacity:1'; }
                        else { return 'stop-color:rgb(0,0,0);stop-opacity:1'; }
                    });
                gradient
                    .append("svg:stop")
                    .attr('offset', '50%')
                    .attr('style', function (d) {
                        if (d.data.traffic.inOctets_css) { return 'stop-color:rgb(' + d.data.traffic.inOctets_css + ');stop-opacity:1'; }
                        else { return 'stop-color:rgb(0,0,0);stop-opacity:1'; }
                    });
                gradient
                    .append("svg:stop")
                    .attr('offset', '51%')
                    .attr('style', function (d) {
                        if (d.data.traffic.outOctets_css) { return 'stop-color:rgb(' + d.data.traffic.outOctets_css + ');stop-opacity:1'; }
                        else { return 'stop-color:rgb(0,0,0);stop-opacity:1'; }

                    });
                gradient
                    .append("svg:stop")
                    .attr('offset', '100%')
                    .attr('style', function (d) {
                        if (d.data.traffic.outOctets_css) { return 'stop-color:rgb(' + d.data.traffic.outOctets_css + ');stop-opacity:1'; }
                        else { return 'stop-color:rgb(0,0,0);stop-opacity:1'; }
                    });
                self.s_link.append("svg:line")
                    .attr("class", function (d, i) {
                        var speed = d.data.link_speed;
                        var classes = "";
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
                    .attr('stroke', function (d, i) {
                        return 'url(#linkload' + i + ')';
                    })
                    .on("click", function(d) {
                        if (self.selected_vlan) {
                            self.updateRenderVLAN(d.data.uplink.vlans);
                        }
                        self.broker.trigger("netmap:selectedLink",  {'link': d, 'selectedVlan': self.selected_vlan});
                    })
                    .on("mouseover", function (d) {
                        if (self.ui.mouseover.links) {
                            if (self.selected_vlan) {
                                self.updateRenderVLAN(d.data.uplink.vlans);
                            }
                            self.broker.trigger("netmap:selectedLink",  {'link': d, 'selectedVlan': self.selected_vlan});
                        }
                    });
            });
            self.s_link.exit().remove();
        },
        updateRenderNodes: function () {
            var self = this;
            self.node_s = self.nodeGroup.selectAll("g.node").data(self.modelJson.nodes, function (d) {
                return d.data.sysname;
            });
            var nodeGroup = self.node_s.enter()
                .append("svg:g")
                .attr("class", "node");
            nodeGroup.append("svg:image")
                .attr("class", "circle node")
                .attr("xlink:href", function (d) {
                    return "/images/netmap/" + d.data.category.toLowerCase() + ".png";
                })
                .attr("x", "-16px")
                .attr("y", "-16px")
                .attr("width", "32px")
                .attr("height", "32px");
            nodeGroup.
                append("svg:text")
                    .attr("dy", "1.5em")
                    .attr("class", "node")
                    .attr("text-anchor", "middle")
                    .attr("fill", "#000000")
                    .attr("background", "#c0c0c0")
                    .text(function (d) {
                        return d.name;
                    });

            self.node_s.exit().remove();
        },
        draw: function (data) {
            var self = this;
            var json = data;

            self.svg.attr("transform",
                "translate(" + self.trans + ") scale(" + self.scale + ")");


            self.force.nodes(json.nodes).links(json.links).on("tick", tick);

            self.force.on('start', function () {
                self.broker.trigger("map:forceChangedStatus", true);
            });

            self.force.on('end', function () {
                self.broker.trigger("map:forceChangedStatus", false);
            });

            self.updateRenderTopologyErrors();

            self.updateRenderLinks();

            var link = self.linkGroup.selectAll("g.link line");

            self.updateRenderNodes();

            var node_drag =
                d3.behavior.drag()
                    .on("dragstart", dragstart)
                    .on("drag", dragmove)
                    .on("dragend", dragend);


            var node = self.svg.selectAll("g.node");

            node
                .on("click", node_onClick)
                .call(node_drag)
                // doubleclick? http://jsfiddle.net/wfG6k/
                .on("mouseover", function (d) {
                    if (self.ui.mouseover.nodes) {
                        return node_onClick(d);
                    }

                });

            if (self.selected_node!==null) {
                self.updateRenderGroupByPosition();
            }

            function tick() {
                node.attr("transform", function (d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });

                if (self.nodesInRoom !== undefined) {
                    self.nodesInRoom
                        .attr("cx", function (d) { return d.px;})
                        .attr("cy", function (d) { return d.py;});
                }

                if (self.selected_vlan) {
                    self.nodesInVlan
                        .attr("cx", function (d) { return d.px;})
                        .attr("cy", function (d) { return d.py;});
                    self.linksInVlan
                        .attr("x1", function (d) { return d.source.x;})
                        .attr("y1", function (d) { return d.source.y;})
                        .attr("x2", function (d) { return d.target.x;})
                        .attr("y2", function (d) { return d.target.y;});
                }

                if (self.linkErrors && self.options.mapProperties.get('displayTopologyErrors', false)) {
                    self.linkErrors
                        .attr("x1", function (d) { return d.source.x; })
                        .attr("y1", function (d) { return d.source.y; })
                        .attr("x2", function (d) { return d.target.x; })
                        .attr("y2", function (d) { return d.target.y; });
                }

                link
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



            }

            var isDragMovedTriggered;
            function dragstart(d, i) {
                isDragMovedTriggered = false;
            }

            function dragmove(d, i) {
                isDragMovedTriggered = true;
                d.px += d3.event.dx;
                d.py += d3.event.dy;
                d.x += d3.event.dx;
                d.y += d3.event.dy;

                self.force.stop();
                d.fixed = true;

                tick();
            }

            function dragend(d, i) {
                tick();

                if (isDragMovedTriggered) {
                    self.force.resume();
                    // uncomment if you don't want node to be auto selected when it is dragged.
                    //if (self.selected_node && d.data.sysname === self.selected_node.data.sysname) {
                    node_onClick(d);
                    //}

                }
            }

            function node_mouseOver(d) {
                mouseFocusInPopup({'title': d.name, 'description': '', 'css_description_width': 200});
                highlightNodeNeighbors(d, 0.1);
            }

            function node_mouseOut(d) {
                mouseFocusOutPopup(d);
                highlightNodeNeighbors(d, 1);
            }

            function highlightNodeNeighbors(d, opacity) {
                node.style("stroke-opacity", function (o) {
                    var thisOpacity = isConnected(d, o) ? 1 : opacity;
                    this.setAttribute('fill-opacity', thisOpacity);
                    this.setAttribute('opacity', thisOpacity);

                    var circle = (this.firstElementChild || this.children[0] || {});

                    var text = (this.childNodes[1] || {});

                    var v = circle.textContent;
                    if (d.name == v) {
                        circle.setAttribute("style", "fill: red");
                        text.setAttribute("style", "fill: red");
                    } else {
                        circle.setAttribute('style', "fill: " + fill(d.group));
                        text.setAttribute('style', "fill: #000");
                    }


                    return thisOpacity;
                });


                link.style("stroke-opacity", function (o) {
                    return o.source === d || o.target === d ? 1 : opacity;
                });

            }

            function link_popup(d) {
                var inOctets, outOctets, inOctetsRaw, outOctetsRaw = "N/A"

                if (d.data.traffic['inOctets'] != null) {
                    inOctets = NetmapExtras.convert_bits_to_si(d.data.traffic['inOctets'].raw * 8);
                    inOctetsRaw = d.data.traffic['inOctets'].raw;
                } else {
                    inOctets = inOctetsRaw = 'N/A';
                }
                if (d.data.traffic['outOctets'] != null) {
                    outOctets = NetmapExtras.convert_bits_to_si(d.data.traffic['outOctets'].raw * 8);
                    outOctetsRaw = d.data.traffic['outOctets'].raw;
                } else {
                    outOctets = outOctetsRaw = 'N/A';
                }

                var thiss_vlans = (d.data.uplink.vlans !== null ? d.data.uplink.vlans : 'none');
                var vlans = [];
                _.each(thiss_vlans, function (num, key) { vlans.push(num.vlan); }, vlans);

                mouseFocusInPopup({
                    'title':                 'link',
                    'description':           d.data.uplink.thiss.interface + " -> " + d.data.uplink.other.interface +
                                                 '<br />' + d.data.link_speed +
                                                 '<br />In: ' + inOctets + " raw[" + inOctetsRaw + "]" +
                                                 '<br />Out: ' + outOctets + " raw[" + outOctetsRaw + "]" +
                                                 '<br />Vlans: ' + vlans.join() +
                                                 '<br />Prefix: ' + d.data.uplink.prefix,
                    'css_description_width': 400
                });

            }

            function link_popout(d) {
                mouseFocusOutPopup(d);
            }

            function mouseFocusInPopup(d) {
                //console.log('mouseFocusInPopup!');
                self.$("#pop-up").fadeOut(100, function () {
                    // Popup content
                    self.$("#pop-up-title").html(d.title);
                    self.$("#pop-img").html("23");
                    self.$("#pop-desc").html(d.description).css({'width': d.css_description_width});

                    // Popup position

                    //console.log(scale);
                    //console.log(trans);

                    var popLeft = (d.x * self.scale) + self.trans[0] - 10;//lE.cL[0] + 20;
                    var popTop = (d.y * self.scale) + self.trans[1] + 70;//lE.cL[1] + 70;
                    self.$("#pop-up").css({"left": popLeft, "top": popTop});
                    self.$("#pop-up").fadeIn(100);
                });

            }

            function mouseFocusOutPopup(d) {
                $("#pop-up").fadeOut(50);
                //d3.select(this).attr("fill","url(#ten1)");
            }

            function node_onClick(node) {
                //var netbox_info = new NetboxInfoView({node: node});
                self.selected_node = node;

                if (self.options.mapProperties.get('position').has_targets()) {
                    self.updateRenderGroupByPosition();
                }

                self.broker.trigger("netmap:selectNetbox", {
                    'selectedVlan': self.selected_vlan,
                    'netbox': node
                });
                if (self.selected_vlan) {
                    self.updateRenderVLAN(node.data.vlans);
                }

            }


            self.node_s.exit().remove();
            self.s_link.exit().remove();
            // coordinate helper box
            /*svg
             .append('svg:rect')
             .attr('width', self.w)
             .attr('height', self.h)
             .attr('fill', 'd5d5d5');*/

            //console.log("[Netmap][Debug] Nodes: {0}".format(json.nodes.length));
            //console.log("[Netmap][Debug] Edges: {0}".format(json.links.length));
            /*svg.style("opacity", 1e-6)
             .transition()
             .duration(10000)
             .style("opacity", 1);*/

        },
        render: function () {
            var svg, self;
            self = this;

            //root_chart.attr("opacity", 0.1);

            svg = self.svg;

            //json = {}


            if (self.force !== undefined) {
                self.force.stop();
            }
            if (self.options.mapProperties) {

            if (this.model && this.model.get('links')) {
                self.modelJson = this.model.toJSON();

                // map links to node objects in modelJson!
                // (identifiers in links are node sysnames!)
                for (var i = 0; i < self.modelJson.links.length; i++) {
                    var link = self.modelJson.links[i];
                    for (var j = 0; j < self.modelJson.nodes.length; j++) {
                        var node = self.modelJson.nodes[j];
                        if (node.data.sysname === link.target) {
                            link.target = node;
                        }
                        if (node.data.sysname === link.source) {
                            link.source = node;
                        }
                    }
                }


                self.updateRenderCategories();

                function isConnected(a, b) {
                    return linkedByIndex[a.data.sysname + "," + b.data.sysname] || linkedByIndex[b.data.sysname + "," + a.data.sysname] || a.data.sysname == b.data.sysname;
                }

                self.force = d3.layout.force().gravity(0.1).charge(-2500).linkDistance(250).size([self.w, self.h]);
                self.draw(self.modelJson);
            }
            }
            self.force.start();
            self.broker.trigger("map:loading:done");

            return this;
        },
        close:function () {
            this.force.stop();
            context_selected_map = undefined;
            this.broker.unregister(this);
            $(window).off("resize.app");
            this.$el.unbind();
            this.$el.remove();
        }
    });
    return drawNetmapView;
});






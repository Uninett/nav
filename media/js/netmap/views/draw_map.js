define([
    'jquery',
    'underscore',
    'backbone',
    'backbone_eventbroker',
    'handlebars',
    'netmapextras',
    // Pull in the Collection module from above
    'views/netbox_info',
    'text!templates/draw_map.html'
], function ($, _, Backbone, BackboneEventbroker, Handlebars, NetmapExtras, NetboxInfoView, netmapTemplate ) {

    var drawNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "chart",

        broker: Backbone.EventBroker,
        interests: {
            'map:resize:animate': 'resizeAnimate',
            'map:redraw': 'redraw',
            'map:search': 'search',
            'map:centerGraph': 'centerGraph',
            'map:freezeNodes': 'freezeNodes',
            'map:show_vlan': 'showVlan',
            'map:ui:mouseover:nodes': 'toggleUIMouseoverNodes',
            'map:ui:mouseover:links': 'toggleUIMouseoverLinks',
            'map:loading:context_selected_map': 'clear',
            'map:node:fixed': 'updateNodeFixedStatus',
            'map:fixNodes': 'updateAllNodePositions'
        },
        initialize: function () {
            this.broker.register(this);

            this.model = this.options.context_selected_map.graph;

            this.$el.append(netmapTemplate);
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);

            this.selected_node = null;
            this.selected_vlan = null;
            this.ui = {
                'topologyErrors': false,
                'mouseover': {
                    'nodes': false,
                    'links': false
                }
            };
            this.context_selected_map = this.options.context_selected_map;
            this.sidebar = this.options.view_map_info;
            this.filter_orphans = !this.context_selected_map.display_orphans;

            this.w = this.options.cssWidth;
            this.h = $(window).height() - 350;
            this.force = d3.layout.force()
                .gravity(0.5)
                .distance(2000)
                .charge(-100)
                .size([self.w, self.h]);

            this.trans = [0,0];
            this.scale = 1;
            this.zoom = d3.behavior.zoom();
            // swap .on with .bind for jQuery<1.7
            $(window).on("resize.app", _.bind(this.resize, this));
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
                        self.resize(self.$el.width() - 100);
                    },
                    complete: function () {
                        self.resize(self.$el.width());
                    }
                });
            //$("#netmap_main_view").animate({'margin-left': "{0}px".format(margin)}, 400);
        },
        resize: function (width) {
            if (!isNaN(width)) {
                this.w = width;
            } else {
                this.w = this.$el.width();
            }
            this.h = $(window).height() - 350;

            (this.$el).find('#svg-netmap').attr('width', this.w);
            (this.$el).find('#svg-netmap').attr('height', this.h);
            (this.$el).find('#svg-netmap rect').attr('width', this.w);
            (this.$el).find('#svg-netmap rect').attr('height', this.h);

        },
        search: function (query) {
            this.searchQuery = {
                query: query
            };
            // find related box
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                if (node.data.sysname.search(query) !== -1) {
                    this.searchQuery.zoomTarget = node;
                    break;
                }
            }
            this.trans = [ (-(this.searchQuery.zoomTarget.x * this.scale) + (this.w / 2)), (-(this.searchQuery.zoomTarget.y * this.scale) + (this.h / 2))];
            this.zoom.translate(this.trans);
            this.svg.attr("transform",
                "translate(" + this.trans + ") scale(" + this.scale + ")");
        },
        showVlan: function (nav_vlan_id) {
            this.selected_vlan = nav_vlan_id;
            this.redraw();
        },
        centerGraph: function () {
            this.scale = 1/Math.log(this.modelJson.nodes.length);
            this.trans = [(-this.w / 2) * (this.scale - 1), (-this.h / 2) * (this.scale - 1)];
            this.zoom.scale(this.scale);
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
            /*for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                node.fixed = isFreezing;
            }*/
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
        },
        updateNodeFixedStatus: function (data) {
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                if (node.data.sysname === data.sysname) {
                    node.fixed = data.fixed;
                    break;
                }
            }
        },
        updateAllNodePositions: function (boolean) {
            for (var i = 0; i < this.modelJson.nodes.length; i++) {
                var node = this.modelJson.nodes[i];
                node.fixed = boolean;
            }
            this.sidebar.render();
        },
        redraw: function (options) {
            if (options !== undefined) {
                if (options.filter_orphans !== undefined) {
                    this.filter_orphans = options.filter_orphans;
                }
                if (options.groupby_room !== undefined) {
                    this.groupby_room = options.groupby_room;
                }
                if (options.topologyErrors !== undefined) {
                    this.ui.topologyErrors = options.topologyErrors;
                }
            }

            this.clear();

            this.render();
        },
        render: function () {

            var chart, svg, trans, scale, self, restart;
            self = this;

            chart = this.$el[0],
                r = 6,
                fill = d3.scale.category20();





            // clean up listners, crappy listners! :D
            /*console.log("cleaning listernersnrsnres");
             $(svg.selectAll("g.node")).unbind();*/
            //debugger;
            //$(d3.select("#svg-netmap")).unbind();
            //d3.select((this.$el).find('#svg-netmap')).remove();
            //this.$el.unbind();


            //this.$el.unbind();
            //d3.select(this.el).remove();
            //debugger;
            //debugger;


//            if (svg === undefined) {


            var root_chart = d3.select(this.el)
                .append("svg:svg")
                .attr('id', 'svg-netmap')
                .attr("width", self.w).attr("height", self.h)
                .attr("pointer-events", "all");
            root_chart
                .append('svg:rect')
                .attr('width', self.w)
                .attr('height', self.h)
                .attr('fill', 'white')
                .call(self.zoom.on("zoom", redraw));
            svg = root_chart.append('svg:g')
                //.call(d3.behavior.zoom().on("zoom", redraw))
                .append('svg:g')
            ;
            //root_chart.attr("opacity", 0.1);
            this.svg = svg;
            /*                if (self.force !== undefined) {
             self.force.off("tick", null);
             }
             $(self.svg).unbind();
             $(self.svg).remove();
             self.svg = svg;


             //console.log("Creating SVG vis");
             }*/


            function redraw() {
                self.trans = d3.event.translate;
                self.scale = d3.event.scale;
                self.context_selected_map.map.set({
                    'zoom': self.trans + ";" + self.scale
                }, {silent: true});
                svg.attr("transform",
                    "translate(" + self.trans + ") scale(" + self.scale + ")");
            }

            //json = {}
            var validateTranslateScaleValues = function (nodesCount) {
                if (isNaN(self.scale)) {
                    console.log("[Netmap][WARNING] Received invalid scale, use default scaling: {0}".format(self.scale));
                    if (nodesCount) {
                        self.scale = 1 / Math.log(nodesCount);
                    } else {
                        self.scale = 1;
                    }
                }
                if (self.trans.length !== 2 || isNaN(self.trans[0]) || isNaN(self.trans[1])) {
                    console.log("[Netmap][WARNING] Received invalid translate values, centering graph: {0}".format(self.trans));
                    self.trans = [(-self.w / 2) * (self.scale - 1), (-self.h / 2) * (self.scale - 1)];
                }
            }

            var draw = function (data) {
                json = data;

                svg.attr("transform",
                    "translate(" + self.trans + ") scale(" + self.scale + ")");

                //svg.attr("transform", "translate({0}) scale({1})".format(self.zoom.trans, self.zoom.scale));


                // FILTERS ON CATEGORIES ---- EXTRACT METHOD PLEASE
                // FILTERS ON CATEGORIES ---- EXTRACT METHOD PLEASE

                self.force.nodes(json.nodes).links(json.links).on("tick", tick);

                if (linkErrors !== undefined && !self.ui.topologyErrors) {
                    linkErrors.exit().remove();
                } else if (self.ui.topologyErrors) {
                    var linkGroupMeta = svg.append("svg:g").attr("class", "linksmeta");

                    var linksWithErrors = self.modelJson.links.filter(function (d) {
                        if (d.data.tip_inspect_link) {
                            return true;
                        }
                        return false;
                    });

                    var linkErrors = linkGroupMeta.selectAll("g line").data(linksWithErrors, function (d) {
                        return d.source.id + "-" + d.target.id;
                    });

                    linkErrors.enter().append("svg:line").attr("class", "warning_inspect");
                    linkErrors.exit().remove();
                }

                var linkGroup = svg.append("svg:g").attr("class", "links");
                //0-100, 100-512,512-2048,2048-4096,>4096 Mbit/s
                var s_link = linkGroup.selectAll("g line").data(json.links, function (d) {
                    return d.source.id + "-" + d.target.id;
                });

                s_link.enter().append("svg:g").attr("class", "link").forEach(function (d, i) {
                    var gradient = s_link
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
                            if (d.data.traffic.inOctets_css) return 'stop-color:rgb(' + d.data.traffic.inOctets_css + ');stop-opacity:1'
                            else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                        });
                    gradient
                        .append("svg:stop")
                        .attr('offset', '50%')
                        .attr('style', function (d) {
                            if (d.data.traffic.inOctets_css) return 'stop-color:rgb(' + d.data.traffic.inOctets_css + ');stop-opacity:1'
                            else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                        });
                    gradient
                        .append("svg:stop")
                        .attr('offset', '51%')
                        .attr('style', function (d) {
                            if (d.data.traffic.outOctets_css) return 'stop-color:rgb(' + d.data.traffic.outOctets_css + ');stop-opacity:1'
                            else return 'stop-color:rgb(0,0,0);stop-opacity:1'

                        });
                    gradient
                        .append("svg:stop")
                        .attr('offset', '100%')
                        .attr('style', function (d) {
                            if (d.data.traffic.outOctets_css) return 'stop-color:rgb(' + d.data.traffic.outOctets_css + ');stop-opacity:1'
                            else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                        });
                    s_link.append("svg:line")
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
                                removeVlanSelectionOnChanged(d.data.uplink.vlans);
                            }
                            self.sidebar.swap_to_link(d);
                        })
                        .on("mouseover", function (d) {
                            if (self.ui.mouseover.links) {
                                if (self.selected_vlan) {
                                    removeVlanSelectionOnChanged(d.data.uplink.vlans);
                                }
                                return self.sidebar.swap_to_link(d);
                            }
                        });
                     /*.on("mouseover", function(d) { return link_popup(d); }) // adds about 400 listners^n refresh :D
                     .on("mouseout", function(d) { return link_popout(d); });*/
                });

                var link = linkGroup.selectAll("g.link line");

                var selectedNodeGroup = svg.append("svg:g").attr("class", "selected_nodes");
                var nodeGroup = svg.append("svg:g").attr("class", "nodes");

                var node_s = nodeGroup.selectAll("g.node").data(json.nodes, function (d) {
                    return d.data.sysname;
                });
                /*var drag = d3.behavior.drag()
                      .origin(Object)
                .call(d3.behavior.zoom().on("zoom", redraw))*/
                var node_drag =
                    d3.behavior.drag()
                        .on("dragstart", dragstart)
                        .on("drag", dragmove)
                        .on("dragend", dragend);


                node_s.enter()
                    .append("svg:g")
                    .attr("class", "node")
                    .append("svg:image")
                    .attr("class", "circle node")
                    .attr("xlink:href", function (d) {
                        return "/images/netmap/" + d.data.category.toLowerCase() + ".png";
                    })
                    .attr("x", "-16px")
                    .attr("y", "-16px")
                    .attr("width", "32px")
                    .attr("height", "32px");

                node_s.enter().forEach(function (d) {
                    node_s.append("svg:text")
                        .attr("dy", "1.5em")
                        .attr("class", "node")
                        .attr("text-anchor", "middle")
                        .attr("fill", "#000000")
                        .attr("background", "#c0c0c0")
                        .text(function (d) {
                            return d.name;
                        });
                });
                var node = svg.selectAll("g.node");

                node
                    .on("click", node_onClick)
                    .call(node_drag)
                    // doubleclick? http://jsfiddle.net/wfG6k/
                    .on("mouseover", function (d) {
                        if (self.ui.mouseover.nodes) {
                            return node_onClick(d);
                            //return node_mouseOver(d);
                        }

                    })
                    .on("mouseout", function (d) {
                        /*if (this.ui.mouseover.nodes) {
                            return self.sidebar.swap_to_netbox(d);
                        }*/
                        //return node_mouseOut(d);
                    })

                ;
                /*node.selectAll("circle").append("title").text(function (d) {
                 return d.name;
                 });*/

                var markVlan = function (selected_vlan) {
                    if (!selected_vlan) {
                        self.nodesInVlan.remove();
                        self.linksInVlan.remove();
                    }
                    var markVlanNodes = self.modelJson.nodes.filter(function (d) {
                        if (d.data.vlans !== undefined && d.data.vlans) {
                            for (var i = 0; i < d.data.vlans.length; i++) {
                                var vlan = d.data.vlans[i];
                                if (vlan.nav_vlan === selected_vlan) {
                                    return true;
                                }
                            }
                        }
                        return false;
                    });

                    var markVlanLinks = self.modelJson.links.filter(function (d) {
                        if (d.data.uplink.vlans !== undefined && d.data.uplink.vlans) {
                            for (var i = 0; i < d.data.uplink.vlans.length; i++) {
                                var vlan = d.data.uplink.vlans[i];
                                if (vlan.nav_vlan === selected_vlan) {
                                    return true;
                                }
                            }
                        }
                        return false;
                    });

                    self.nodesInVlan = selectedNodeGroup.selectAll("g circle").data(markVlanNodes, function (d) {
                        return d.data.sysname;
                    });

                    self.linksInVlan = svg.selectAll("g links").data(markVlanLinks, function (d) {
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
                        .attr("class", "grouped_by_vlan");

                    self.nodesInVlan.exit().remove();
                };

                if (self.selected_vlan !== undefined && self.selected_vlan) {
                    markVlan(self.selected_vlan);
                }



                var groupByRoom = function () {
                    var groupByRoomId = self.modelJson.nodes.filter(function (d) {
                        return d.data.roomid === self.selected_node.data.roomid
                    });

                    self.nodesInRoom = svg.selectAll("g circle").data(groupByRoomId, function (d) {
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
                };
                if (self.groupby_room && self.selected_node!==null) {
                    groupByRoom();
                }
                //spinner.stop();


                function tick() {

                    /*if (self.force.alpha()<0.03) {
                        root_chart.attr("opacity", 1);
                    }*/

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

                    if (self.ui.topologyErrors) {
                        linkErrors
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

                    //node.call( function (d,i) { return node_drag(d,i) });


                }

                var dragInfo ;
                function dragstart(d, i) {
                    dragInfo = {
                        x: Math.abs(d.x),
                        y: Math.abs(d.y)
                    };
                    //self.force.stop();
                    self.force.friction(0);
                }

                function dragmove(d, i) {
                    d.px += d3.event.dx;
                    d.py += d3.event.dy;
                    d.x += d3.event.dx;
                    d.y += d3.event.dy;
                    tick();
                }

                function dragend(d, i) {
                    tick();

                    if (nodeIsDragged(d)) {
                        d.fixed = true;
                        if (self.selected_node && d.data.sysname === self.selected_node.data.sysname) {
                            node_onClick(d);
                        }

                    }

                    self.force.friction(0.9);
                    if (nodeIsDragged(d)) {
                        self.force.resume();
                    }


                }

                var nodeIsDragged = function (d) {
                    console.log(dragInfo.x, Math.abs(d.x));
                    return ((dragInfo.x - Math.abs(d.x) > 2) || (dragInfo.y - Math.abs(d.y) > 2));
                };

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
                        thisOpacity = isConnected(d, o) ? 1 : opacity;
                        this.setAttribute('fill-opacity', thisOpacity);
                        this.setAttribute('opacity', thisOpacity);

                        circle = (this.firstElementChild || this.children[0] || {})

                        text = (this.childNodes[1] || {})

                        v = circle.textContent
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
                    self.sidebar.swap_to_netbox(node);

                    if (self.groupby_room) {
                        groupByRoom();
                    }

                    if (self.selected_vlan) {
                        removeVlanSelectionOnChanged(node.data.vlans);
                    }

                    //self.sidebar.html(netbox_info.render().el);
                }

                var removeVlanSelectionOnChanged = function (vlans) {
                    var foundVlan = false;
                    if (vlans !== undefined && vlans) {
                        for (var i = 0; i < vlans.length; i++) {
                            var vlan = vlans[i];
                            if (self.selected_vlan === vlan.nav_vlan) {
                                foundVlan = true;
                                break;
                            }
                        }
                    }
                    if (!foundVlan) {
                        self.selected_vlan = null;
                        markVlan(self.selected_vlan);
                    }
                };

                self.force.stop();
                node_s.exit().remove();
                s_link.exit().remove();

                // coordinate helper box
                /*svg
                    .append('svg:rect')
                    .attr('width', self.w)
                    .attr('height', self.h)
                    .attr('fill', 'd5d5d5');*/

                console.log("[Netmap][Debug] Nodes: {0}".format(json.nodes.length));
                console.log("[Netmap][Debug] Edges: {0}".format(json.links.length));
                self.force.start();
                /*svg.style("opacity", 1e-6)
                 .transition()
                 .duration(10000)
                 .style("opacity", 1);*/

            };


            // http://stackoverflow.com/a/8683287/653233
            // intersectionObjects() for the intersection of objects
            // using your equality function of choice
            function intersectionObjects2(a, b, areEqualFunction) {
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

            function intersectionObjects() {
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
            }

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
                        isNodeMatchingFilter = false;
                        for (var k = 0; k < selected_categories.length; k++) {
                            var selected_category = selected_categories[k];
                            if (selected_category.toLowerCase() === node.data.category.toLowerCase()) {
                                isNodeMatchingFilter = true;
                                break;
                                // remove? need to reorder index crap..
                            }
                        }
                        if (isNodeMatchingFilter) {
                            result.push(node);
                        } else if (!node.fixed) {
                            // reset it's coordinates if position is not fixed
                            // and it doesn't match filter.

                            /*node.x = 0;
                             node.y = 0;*/

                        }

                    } else {
                        console.log("THIS IS A BUG");
                        console.log(i);
                    }
                }
                return result;
            }




            function categoryLinksFilter(data, filter_nodes, selected_categories) {
                var json = data;
                //if (!self.selected_netmap.isNew() && self.selected_netmap.attributes.)

                //var selected_categories = ['other','sw'];

                // can't remove nodes YET, will screw up stupid linksLinkedByIndex!
                // If you don't want to remap links >=index_you_delete by -1 for every
                // delete ...


                var filter_links = [];




                var filter_nodes_indexes = filter_nodes;

                /**
                 * Create new d3_json format:
                 *
                 *
                 * add new node
                 *   add links related to node matching CRITERIA with new index
                 *   run thru already added links & update indexes
                 *
                 *
                 */
                function filterLinks() {
                    var result = [];

                    function isMatchingCriteria() {
                        var sourceMatch = false;
                        var targetMatch = false;
                        var source, target;
                        source = link.source;
                        target = link.target;


                        for (var z = 0; z < selected_categories.length; z++) {
                            var selected_category = selected_categories[z].toLowerCase();
                            if (source.data.category.toLowerCase() === selected_category) {
                                sourceMatch = true;
                            }
                            if (target.data.category.toLowerCase() === selected_category) {
                                targetMatch = true;
                            }
                        }
                        return sourceMatch && targetMatch;

                    }

                    console.log(filter_nodes_indexes);
                    console.log("START: " + json.links.length);
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
                    console.log("result : " + result.length);
                    return result;
                }

                filter_links = filterLinks();

                return filter_links;
            }



            //var selected_categories = context_selected_map.map.
            //var selected_categories = ['gsw', 'sw'];
            if (self.force !== undefined) {
                self.force.stop();
            }

            var selected_categories = self.context_selected_map.map.attributes.categories;

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


            // Category filter, finds nodes to keep, filters em out and
            // remaps links
            var keepNodes = filterNodes(self.modelJson, selected_categories);
            self.modelJson.nodes = intersectionObjects(
                self.modelJson.nodes,
                keepNodes,
                function (a, b) {
                    return a.data.sysname === b.data.sysname;
                });
            self.modelJson.links = categoryLinksFilter(self.modelJson, keepNodes, selected_categories);

            var linkedByIndex = {};
            self.modelJson.links.forEach(function (d) {
                linkedByIndex[d.source.data.sysname + "," + d.target.data.sysname] = 1;
            });

            function isConnected(a, b) {
                return linkedByIndex[a.data.sysname + "," + b.data.sysname] || linkedByIndex[b.data.sysname + "," + a.data.sysname] || a.data.sysname == b.data.sysname;
            }

            if (self.filter_orphans) {
                console.log("Filtering orphans");
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

            }



            var getMapOptions = function (nodesCount) {
                // translate and scale to saved settings
                if (!self.context_selected_map.map.isNew() && self.context_selected_map.map.attributes.zoom !== undefined) {
                    var tmp = self.context_selected_map.map.attributes.zoom.split(";");
                    self.trans = tmp[0].split(",");
                    self.scale = tmp[1];
                    validateTranslateScaleValues(nodesCount);
                    self.zoom.translate(self.trans);
                    self.zoom.scale(self.scale);

                    svg.attr("transform",
                        "translate(" + self.trans + ") scale(" + self.scale + ")");

                } else {
                    // adjust scale and translated according to how many nodes
                    // we're trying to draw

                    // Guess a good estimated scaling factor
                    self.scale = 1 / Math.log(nodesCount);

                    // translate ( -centerX*(factor-1) , -centerY*(factor-1) ) scale(factor)
                    // Example: SVG view pot 800x600, center is 400,300
                    // Reduce 30%, translate( -400*(0.7-1), -300*(0.7-1) ) scale(0.7)
                    self.trans = [(-self.w / 2) * (self.scale - 1), (-self.h / 2) * (self.scale - 1)];

                    validateTranslateScaleValues();
                    self.zoom.scale(self.scale);
                    self.zoom.translate(self.trans);


                }
                self.force = d3.layout.force().gravity(0.1).charge(-2500).linkDistance(250).size([self.w, self.h]);
            }

            getMapOptions(self.modelJson.nodes.length);
            draw(self.modelJson);
            redraw = false;

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






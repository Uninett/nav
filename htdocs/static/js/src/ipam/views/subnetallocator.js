// Major view component for viewing allocated subnets and reserving available
// ranges. Might be refactored into a standalone app at some point.
//
// A quick note about the architecture: This component is modelled as a simple
// state machine, using a simple homegrown shim (statist.js). Most actions,
// events will be handled by triggering a certain signal within the FSM,
// ensuring we always maintain a consistent state.

define(function(require, exports, module) {

  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");
  var Foundation = require("libs/foundation.min");
  var d3 = require("d3v4");
  var debug = require("src/ipam/util").ipam_debug.new("views:available_subnets");

  var Models = require("src/ipam/models");

  // For simplicity reasons, use a state singleton


  var viewStates = {
    INIT: {
      SHOW_TREEMAP: "SHOWING_TREEMAP"
    },
    SHOWING_TREEMAP: {
      HIDE: "HIDING_TREEMAP",
      FOCUS_NODE: "FOCUSED_NODE"
    },
    HIDING_TREEMAP: {
      DONE: "INIT"
    },
    CREATING_RESERVATION: {
      CHOOSE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE",
      HIDE: "HIDING_RESERVATION"
    },
    CHOSEN_RESERVATION_SIZE: {
      SEND: "SENDING_RESERVATION"
    },
    SENDING_RESERVATION: {
      RESET: "INIT"
    },
    HIDING_RESERVATION: {
      DONE: "FOCUSED_NODE"
    },
    FOCUSED_NODE: {
      RESET: "INIT",
      RESERVE: "CREATING_RESERVATION",
      FOCUS_NODE: "FOCUSED_NODE"
    }
  };

  var AvailableSubnetsView = Marionette.LayoutView.extend({
    debug: debug,
    template: "#prefix-available-subnets",

    behaviors: {
      StateMachine: {
        states: viewStates,
        init: function(fsm) {
          var stateMixin = {
            HIDE: "HIDING_RESERVATION",
            HIDE_TREEMAP: "HIDING_TREEMAP",
            FOCUS_NODE: "HIDING_RESERVATION"
          };
          fsm.extends("CREATING_RESERVATION", stateMixin);
          fsm.extends("CHOSEN_RESERVATION_SIZE", stateMixin);
          fsm.extends("SENDING_RESERVATION", stateMixin);
          return fsm;
        },
        modelField: "state",
        handlers: {
          "SHOWING_TREEMAP": "showingTreemap",
          "HIDING_TREEMAP": "hidingTreemap",
          "FOCUSED_NODE": "focusedNode",
          "CREATING_RESERVATION": "creatingReservation",
          "HIDING_RESERVATION": "hideReservation"
        }
      }
    },

    regions: {
      allocationTree: ".allocation-tree:first",
      nodeInfo: ".allocation-tree-info:first",
      reservation: ".allocation-tree-reservation:first"
    },

    initialize: function(opts) {
      var self = this;
      this.model = new Models.AvailableSubnets({
        queryParams: {
          prefix: opts.prefix
        }
      });
      // Log some stuff
      this.debug("Mounted subnet component for", opts.prefix);
      this.fsm.onChange(function(nextState) {
        self.debug("Moving into state", nextState);
      });
      // Start application
      this.fetch();
    },

    focusedNode: function(self, node) {
      self.debug("Focused on", node);
      self.model.set("focused_node", node);
      var payload = {
        node: node,
        fsm: self.fsm
      };
      // Mount/refresh info subview
      self.showChildView("nodeInfo", new InfoView(payload));
    },

    showingTreemap: function(self) {
      self.debug("Showing subnet treemap");
      var target = self.$el.find(".allocation-tree:first");
      var treeMap = target.find(".treemap").get(0);
      var data = self.model.get("raw_data");
      var notify = function(__node) {
        self.fsm.step("FOCUS_NODE", __node);
      };
      // Signal state change, do stuff
      AllocationTreemap({
        data: { prefix: "*", children: data },
        treemapElem: treeMap,
        width: 1024,
        height: 200,
        notify: notify
      });
    },

    hidingTreemap: function(self) {
      self.debug("Hiding subnet treemap");
      self.$el.find(".subnets:first").hide();
      self.model.set("hide", true);
      self.fsm.step(self.fsm.events.DONE);
    },

    creatingReservation: function(self, node) {
      self.debug("Creating reservation for", node);
      var payload = {
        node: node,
        fsm: self.fsm
      };
      // Mount/refresh info subview
      self.showChildView("reservation", new ReservationView(payload));
    },

    // When deleting reservation, just return to new or currently focused node
    hideReservation: function(self, node) {
      self.debug("Destroying reservation");
      self.getRegion("reservation").reset();
      self.fsm.step("DONE", node);
    },

    // STATE MACHINE END

    onReceive: function() {
      this.fsm.step(this.fsm.events.SHOW_TREEMAP);
    },

    fetch: function() {
      this.refetch();
    },

    refetch: function() {
      var prefix = this.model.get("queryParams").prefix;
      this.debug("Trying to get subnets for " + prefix);
      // cache xhr object
      this.xhr = this.model.fetch({reset: true});
      this.xhr.done(this.onReceive.bind(this, this));
    }
  });

  // TODO: Proper model for Reservation, with reservation data etc
  var ReservationView = Marionette.LayoutView.extend({
    template: "#prefix-allocate-reservation",

    events: {
      "click .cancel-reservation:first": "cancelReservation",
      "change .size-of-network:first": "fetchCandidates"
    },

    initialize: function(opts) {
      this.fsm = opts.fsm;
      this.node = opts.node;
      this.model = new Backbone.Model(this.node);
    },

    serializeData: function(opts) {
      return {
        node: this.model.toJSON(),
        state: this.fsm.state
      };
    },

    // Fetch and mount candidates for new prefix reservation
    fetchCandidates: function(evt) {
      var prefix = this.node.prefix;
      var prefixListElem = this.$el.find(".prefix-list");
      var sizeOfNetwork = this.$el.find(".size-of-network").val();
      // TODO handle sizeofnetwork > prefix.length etc
      var url = "/ipam/api/suggest/?n=" + sizeOfNetwork + "&prefix=" + prefix;
      var optionTemplate = _.template("<%= prefix %> (<%= start%>-<%= end %>)");
      prefixListElem.select2({
        dataType: 'json',
        ajax: {
          url: url,
          results: function(data) {
            console.log(data);
            var transformed = _.map(data.candidates, function(prefixMap) {
              return {
                text: optionTemplate(prefixMap),
                id: prefixMap.prefix
              };
            });
            return { results: transformed };
          }
        }
      });
    },

    onAttach: function() {
      // make Foundation detect slider
      $(document).foundation();
    },

    cancelReservation: function() {
      this.fsm.step("HIDE", this.node);
    },

    // Animate stuff
    onBeforeAttach: function() {
      this.$el.fadeIn("slow");
    },
    onBeforeDestroy: function() {
      this.$el.fadeOut("slow");
    }

  });

  var InfoView = Marionette.LayoutView.extend({
    template: "#prefix-allocate-info",

    events: {
      "click .reserve-subnet": "reserveSubnet"
    },

    initialize: function(opts) {
      this.fsm = opts.fsm;
      this.node = opts.node;
      this.model = new Backbone.Model(this.node);
    },

    serializeData: function(opts) {
      return {
        node: this.model.toJSON(),
        state: this.fsm.state
      };
    },

    reserveSubnet: function() {
      this.fsm.step("RESERVE", this.node);
      this.render();
    }

  });

  var viewbox = _.template("0 0 <%= width %> <%= height %>");

  // todo: handle case of tree height = 0, e.g. no subnets (meaning we should be
  // able to partition the prefix)

  var AllocationTreemap = function(opts) {
    var width = opts.width;
    var height = opts.height;
    var mountElem = opts.treemapElem;
    var data = opts.data.children[0];
    // callback fn
    var notify = opts.notify;

    var xScale = d3.scaleLinear().range([0, width]);
    var yScale = d3.scaleLinear().range([0, height]);

    var getWidth = function(d) {
      return d.x1 - d.x0;
    };

    // split into hierarchical data
    var partition = d3.partition();
    var root = d3.hierarchy(data);

    root.each(function (node) {
      if (typeof node.data.prefixlen === "undefined") return;
      node.value = Math.pow(2, 32 - node.data.prefixlen);
    });
    partition(root);

    var svg = d3.select(mountElem)
          .append("svg")
          .attr("viewBox", viewbox({width: width, height: height}))
          .attr("class", "matrix")
          .append("g");

    var subnet = svg.selectAll("g")
          .data(root.descendants())
          .enter()
          .append("g")
          .attr("class", "matrix-subnet")
          .attr("transform", function(d) { return "translate(" + xScale(d.x0) + "," + yScale(d.y0) + ")"; });

    var subnetRect = subnet.append("rect")
          .attr("class", "matrix-subnet-rect")
          .attr("width", function(d) { return xScale(d.x1 - d.x0); })
          .attr("height", function(d) { return yScale(d.y1 - d.y0); })
          .attr("fill", colors)
          .attr("stroke", function(d) { return colors(d).darker(1); })
          .on("click", zoom);

    var subnetText = subnet.append("text");

    var subnetPrefix = subnetText.append("tspan")
          .attr("class", "matrix-subnet-prefix")
          .attr("visibility", function(d) {
            return xScale(getWidth(d)) > 30 ? "visible" : "hidden";
          })
          .text(function(d) {
            var _width = xScale(getWidth(d));
            if (_width > 100) {
              return d.data.prefix;
            } else if (_width > 50) {
              return "." + d.data.last_octet + "/" + d.data.prefixlen;
            } else {
              return null;
            }
          });

    // Center text
    subnetText.selectAll("tspan")
      .attr("x", function(d) { return 0.5 * (xScale(d.x1) - xScale(d.x0)); })
      .attr("y", function(d) { return 0.5 * (yScale(d.y1) - yScale(d.y0)); });

    // Enter + update pattern?
    function zoom(d) {
      notify(d.data);
      var xMask = 100;
      xScale.domain([d.x0, d.x0 + (d.x1 - d.x0)]).range([d.x0 ? xMask : 0, width - xMask]);
      yScale.domain([d.y0, 1]).range([d.y0 ? 20 : 0, height]);
      subnet.transition()
        .duration(750)
        .attr("transform", function(d) { return "translate(" + xScale(d.x0) + "," + yScale(d.y0) + ")"; });
      subnetRect.transition()
        .duration(750)
        .attr("width", function(d) { return xScale(d.x1) - xScale(d.x0); })
        .attr("height", function(d) { return yScale(d.y1) - yScale(d.y0); });

      subnetText.selectAll("tspan").transition()
        .duration(750)
        .attr("visibility", function(d) {
          return xScale(d.x0 + (d.x1 - d.x0)) - xScale(d.x0) > 30 ? "visible" : "hidden";
        })
        .attr("x", function(d) { return 0.5 * (xScale(d.x1) - xScale(d.x0)); })
        .attr("y", function(d) { return 0.5 * (yScale(d.y1) - yScale(d.y0)); })
        .text(function(d) {
          var _width = xScale(d.x1) - xScale(d.x0);
          if (_width > 100) {
            return d.data.prefix;
          } else if (_width > 50) {
            return "." + d.data.last_octet + "/" + d.data.prefixlen;
          } else {
            return "";
          }
        });
    }
  };

  // Maps different types of nodes to different colors
  function colors(d) {
    if (d.depth === 0) {
      return d3.hsl(80, 1, 0.5);
    }
    if (d.data.net_type === "available") {
      return d3.hsl(120, 1, 0.5);
    }
    if (d.data.net_type === "scope") {
      return d3.hsl(0, 0, 0.87);
    }
    return d3.hsl(0, 0, .5);
  }

  module.exports = AvailableSubnetsView;

});

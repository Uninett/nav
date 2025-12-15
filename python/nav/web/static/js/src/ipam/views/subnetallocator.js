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
  var debug = require("src/ipam/util").ipam_debug.new("views:available_subnets");

  var Models = require("src/ipam/models");
  var PrefixMap = require("src/ipam/views/prefixmap");

  // Event broker
  var globalCh = Backbone.Wreqr.radio.channel("global");

  // For simplicity reasons, use a state singleton
  var viewStates = {
    INIT: {
      FETCH_STATS: "FETCHING_STATS",
      SHOW_TREEMAP: "SHOWING_TREEMAP"
    },
    FETCHING_STATS: {
      FETCHING_DONE: "SHOWING_TREEMAP"
    },
    SHOWING_TREEMAP: {
      HIDE: "HIDING_TREEMAP",
      FOCUS_NODE: "FOCUSED_NODE"
    },
    HIDING_TREEMAP: {
      DONE: "INIT"
    },
    CREATING_RESERVATION: {
      FOCUS_NODE: "HIDING_RESERVATION",
      HIDE: "HIDING_RESERVATION"
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

  // Main container for subnet allocator.
  var AvailableSubnetsView = Marionette.LayoutView.extend({
    debug: debug,
    template: "#prefix-available-subnets",

    behaviors: {
      StateMachine: {
        states: viewStates,
        modelField: "state",
        handlers: {
          "SHOWING_TREEMAP": "showingTreemap",
          "HIDING_TREEMAP": "hidingTreemap",
          "FOCUSED_NODE": "focusedNode",
          "CREATING_RESERVATION": "creatingReservation",
          "HIDING_RESERVATION": "hideReservation",
          "FETCHING_STATS": "fetchingStats"
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
      // Start application by fetching
      this.fetch();
    },

    // STATE MACHINE START

    // When we're focused on a particular node in the tree and displaying some
    // information about it
    focusedNode: function(self, node) {
      self.debug("Focused on", node);
      self.model.set("focused_node", node);
      var payload = {
        node: node,
        fsm: self.fsm
      };
      /*
        TODO: Upgrade Marionette version to latest stable - 3.x or 4.x.
        The codebase was updated to use jQuery 3.x, which has compatibility issues with Marionette regions.
        Therefore, we bypass Marionette regions here and directly manipulate the DOM using jQuery.

        Upgrading Marionette requires a significant refactoring effort and thorough testing to ensure
        compatibility with the existing codebase. Once upgraded, we can revert to using Marionette regions for better
        view management and lifecycle handling.
      */
      const infoContainer = self.$el.find(".allocation-tree-info:first");
      if (infoContainer.length === 0) {
        console.warn("nodeInfo container not found in DOM");
        return;
      }
      const infoView = new InfoView(payload);
      infoView.render();
      infoContainer.html(infoView.$el);
    },

    // Initial state. The tree has the data it needs to draw itself.
    showingTreemap: function(self) {
      self.render();
      self.debug("Showing subnet treemap");
      var target = self.$el.find(".allocation-tree:first");
      var treeMap = target.find(".treemap").get(0);
      var data = self.model.get("raw_data");
      var notify = function(__node) {
        if (__node.net_type == "scope") {
          globalCh.vent.trigger("scrollto", __node);
        }
        self.fsm.step("FOCUS_NODE", __node);
      };
      // Signal state change, do stuff
      PrefixMap({
        data: { prefix: "*", children: data },
        mountElem: treeMap,
        width: 1024,
        height: 200,
        selectNodeCallBack: notify
      });
      // Ensure htmx processes the opened tree to enable hx-* attributes
      htmx.process(self.$el.get(0));
    },

    hidingTreemap: function(self) {
      self.debug("Hiding subnet treemap");
      self.$el.find(".subnets:first").hide();
      self.model.set("hide", true);
      self.fsm.step(self.fsm.events.DONE);
    },

    // The user is trying to reserve a new prefix for some particular purpose
    creatingReservation: function(self, node) {
      self.debug("Creating reservation for", node);
      var payload = {
        node: node,
        fsm: self.fsm
      };
      // Find the region element and render the ReservationView into it
      // (bypassing Marionette regions due to jQuery 3.x compatibility issues)
      const reservationContainer = self.$el.find(".allocation-tree-reservation:first");
      if (reservationContainer.length === 0) {
        console.warn("reservation container not found in DOM");
        return;
      }
      const reservationView = new ReservationView(payload);
      reservationView.render();
      reservationContainer.html(reservationView.$el);
      // Store reference for cleanup
      self._reservationView = reservationView;
    },

    // When deleting reservation, just return to new or currently focused node
    hideReservation: function(self, node) {
      self.debug("Destroying reservation");
      // Clean up reservation view manually
      if (self._reservationView) {
        self._reservationView.destroy();
        self._reservationView = null;
      }
      self.$el.find(".allocation-tree-reservation:first").empty();
      self.fsm.step("DONE", node);
    },

    // Loading state, e.g. trying to get some data to display to the user
    fetchingStats: function(self) {
      var prefix = self.model.get("queryParams").prefix;
      self.debug("Trying to get subnets for " + prefix);
      // cache xhr object
      self.xhr = self.model.fetch({reset: true});
      self.xhr.done(self.onReceive.bind(this, self));
    },

    // STATE MACHINE END

    onBeforeDestroy: function() {
      // Kill pending fetches upon destroying this component
      if (!_.isUndefined(this.xhr)) {
        this.xhr.abort();
      }
    },

    onReceive: function(self) {
      self.fsm.step(self.fsm.events.FETCHING_DONE);
    },

    fetch: function() {
      this.fsm.step("FETCH_STATS");
    }
  });


  var reservationStates = {
    INIT: {
      CHOOSE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE",
      STORE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE"
    },
    CHOSEN_RESERVATION_SIZE: {
      CHOOSE_SUBNET: "CHOSEN_SUBNET",
      CHOOSE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE",
      STORE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE"
    },
    CHOSEN_SUBNET: {
      CHOOSE_SUBNET: "CHOSEN_SUBNET",
      CHOOSE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE",
      STORE_RESERVATION_SIZE: "CHOSEN_RESERVATION_SIZE"
    }
  };

  var ReservationView = Marionette.LayoutView.extend({
    template: "#prefix-allocate-reservation",
    baseUrl: "/seeddb/prefix/add/?",

    behaviors: {
      StateMachine: {
        states: reservationStates
      }
    },

    events: {
      "change .size-of-network": "onNetworkSizeChange",
      "keypress .size-of-network": "onNetworkSizeKeypress",
      "click .cancel-reservation:first": "cancelReservation",
      "select2:select .prefix-list": "onSelectPrefix",
      "click .choose-network-size": "chooseNetworkSize"
    },

    initialize: function(opts) {
      this.parent_fsm = opts.fsm;
      this.node = opts.node;
      this.model = new Backbone.Model(this.node);
      this.model.set("creation_url", null);
      // Since template uses states, rerender on new state
      this.fsm.onChange(this.render);
      this.fsm.onChange(function (state) {
        console.log("RESERVATION went into state", state);
      });
    },

    onNetworkSizeKeypress: function(evt) {
      if (evt.which === 13) {
        this.chooseNetworkSize(evt);
      }
    },

    chooseNetworkSize: function(evt) {
      evt.preventDefault();
      this.getAndStoreNetworkSize();
      var networkSize = this.model.get("network_size");
      if (networkSize === '' || !networkSize) {
        return;
      }
      this.fsm.step("CHOOSE_RESERVATION_SIZE");
    },

    onNetworkSizeChange: function(evt) {
      evt.preventDefault();
      this.getAndStoreNetworkSize();
      this.fsm.step("STORE_RESERVATION_SIZE");
    },

    getAndStoreNetworkSize: function() {
      var sizeOfNetwork = this.$el.find(".size-of-network").val();
      this.model.set("network_size", sizeOfNetwork);
      this.model.set("selected_prefix", null);
    },

    onSelectPrefix: function(evt) {
      // Don't handle empty values from user
      // In Select2 v4, the selected data is in evt.params.data
      const selectedData = evt.params?.data;
      if (!selectedData?.id) {
        return;
      }
      const params = {
        "net_address": selectedData.id,
        "net_type": "reserved"
      };
      this.model.set("creation_url", this.baseUrl + decodeURIComponent($.param(params, true)));
      this.model.set("selected_prefix", selectedData.id);
      this.fsm.step("CHOOSE_SUBNET");
    },

    serializeData: function(opts) {
      return {
        node: this.model.toJSON(),
        creation_url: this.model.get("creation_url"),
        selected_prefix: this.model.get("selected_prefix"),
        network_size: this.model.get("network_size"),
        state: this.fsm.state
      };
    },

    onRender: function(self) {
      // Mount select2 if found
      var selectElem = self.$el.find(".prefix-list:first");
      var sizeOfNetwork = self.model.get("network_size");
      var prefix = self.model.get("prefix");
      if (!(sizeOfNetwork && prefix)) {
        return;
      }
      var optionTemplate = _.template("<%= prefix %> (<%= start%>-<%= end %>)");
      var pageSize = 10;
      selectElem.select2({
        placeholder: self.model.get("selected_prefix") || "Select a subnet",
        ajax: {
          url: "/ipam/api/suggest/",
          dataType: 'json',
          data: function(params) {
            const page = params.page || 1;
            return {
              n: pageSize,
              prefixlen: sizeOfNetwork,
              prefix: prefix,
              offset: pageSize * (page - 1)
            };
          },
          processResults: function(data, params) {
            console.log(data);
            const transformed = _.map(data.candidates, function (prefixMap) {
              return {
                text: optionTemplate(prefixMap),
                id: prefixMap.prefix
              };
            });
            params.page = params.page || 1;
            return { results: transformed, pagination: { more: data.more } };
          }
        }
      });
    },

    cancelReservation: function() {
      this.parent_fsm.step("HIDE", this.node);
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


  // This is where the hard part starts: The viz of the network layout. TODO:
  // Consider moving this into a separate file.

  module.exports = AvailableSubnetsView;

});

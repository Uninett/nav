// This file contains all components related to the drawing of the main prefix
// tree. It works recursively, hence the same components (NodeView and TreeView)
// are used to display any descendants of our root nodes.

define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Views = require("src/ipam/views/index");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");


  // Simple utility object to flash messages. Might be moved into utils.js at
  // some point.
  var flash = {
    call: function(klass, msg) {
      globalCh.vent.trigger("flash", klass, msg);
    },

    noResult: function(searchParams) {
      var tmpl = _.template("No results<% if (query) { %> for <strong>'<%- query %>'</strong><% } %>.");
      this.call("alert-box alert with-icon", tmpl({query: searchParams}));
    },

    fetch: function() {
      var tmpl = _.template("<i class='fa fa-spinner fa-spin'></i> <span>Fetching</span>");
      this.call("alert-box", tmpl());
    },

    reset: function() {
      globalCh.vent.trigger("flash:reset");
    }
  };

  // Base of tree (e.g. only top nodes of our prefix tree)
  var RootView = Marionette.LayoutView.extend({
    debug: debug.new("views:rootview"),
    regions: {
      "tree": ".prefix-tree-root"
    },
    template: "#prefix-list",

    // Check if we have an empty tree
    isEmpty: function() {
      return !this.collection || this.collection.length === 0;
    },

    // Handles fetching, cancels previous fetches if any etc.
    refetch: function() {
      // Cancel existing fetches to avoid happy mistakes
      if (typeof this.xhr !== "undefined") {
        this.debug("Aborted previous fetch!");
        this.xhr.abort();
      }
      // Don't fetch if no query params
      if (!this.collection.queryParams) {
        return;
      }
      // Keep a pointer to the fetch object, for tracking all fetches
      this.xhr = this.collection.fetch({reset: true});
      // Hide children while fetching
      this.tree.$el.hide();
      var self = this;
      this.xhr.done(function (){
        self.tree.$el.show();
      });
      flash.fetch();
    },

    initialize: function() {
      // Don't mess with the ordering
      this.sort = false;
      // Don't render before fetch of collection returns
      this.collection = new Models.PrefixNodes();
      this.refetch();
      // Handle reset events, e.g. when a fetch is done
      this.collection.bind("reset", this.onRender, this);
      this.collection.bind("fetch", this.onRender, this);
      // Set up global handlers for requests etc
      var self = this;
      globalCh.vent.on("fetch:all", function() { self.refetch(); });
      globalCh.vent.on("search:update", function(params) {
        self.debug("Got new search params", params);
        self.collection.queryParams = params;
        self.refetch();
      });
      var scrolltoHandler = function(node) {
        self.debug("Trying to scroll to", node);
        var elem = $("#prefix-" + node.pk);
        // Element not found in DOM
        if (!elem.length && node.parent_pk) {
          globalCh.vent.trigger("open_node", node.parent_pk);
          setTimeout(function(){
            scrolltoHandler(node);
          }, 1000);
          return;
        }
        // Calculate offset and move to the desired node
        globalCh.vent.trigger("open_node", node.pk);
        self.debug("Scrolling to", node.pk);
        $("html, body").animate({
          scrollTop: elem.offset().top
        }, "slow");
      };
      globalCh.vent.on("scrollto", scrolltoHandler);
    },

    /* Whether or not we're currently fetching some data */
    isFetching: function() {
      if (typeof this.xhr === "undefined") {
        return false;
      }
      switch (this.xhr.readyState) {
      case 1:
      case 2:
      case 3:
        return true;
      default:
        return false;
      }
    },

    // Defer drawing until we need to show something. This is done to do all our
    // drawing in a single operation, which speeds up rendering and allows us to
    // show the user all the results at once. At some point, it might make sense
    // to consider implementing lazy-loading/pagination as the user scrolls down
    // the tree, but this is overkill for relatively narrow prefix trees.
    onBeforeShow: function() {
      this.showChildView("tree", new TreeView({
        model: new Models.Tree(),
        collection: this.collection
      }));
    },

    // Flash some messages depending on the state of our tree.
    onRender: function() {
      if (this.isFetching()) {
        return flash.fetch();
      }
      if (this.isEmpty() && this.collection.queryParams) {
        var searchParams = this.collection.queryParams.search;
        return flash.noResult(searchParams);
      } else {
        return flash.reset();
      }
    },

    onBeforeDestroy: function() {
      // Kill pending fetches upon destroying this component
      if (!_.isUndefined(this.xhr)) {
        this.xhr.abort();
      }
    }

  });

  // TODO: Do blur using global channel or something
  var nodeViewStates = {
    INIT: {
      "TOGGLE_OPEN": "OPENING_NODE",
      "FETCH_STATS": "FETCHING_STATS"
    },
    OPENING_NODE: {
      "OPENED_NODE": "OPEN_NODE"
    },
    FETCHING_STATS: {
      "DONE_FETCHING_STATS": "LOADING_STATS"
    },
    LOADING_STATS: {
      "DONE_LOADING_STATS": "INIT"
    },
    OPEN_NODE: {
      "SHOW_CHILDREN": "SHOWING_CHILDREN",
      "TOGGLE_OPEN": "CLOSING_NODE"
    },
    CLOSING_NODE: {
      "CLOSED_NODE": "INIT"
    },
    "SHOWING_CHILDREN": {
      "DONE_SHOWING_CHILDREN": "OPEN_NODE",
      "TOGGLE_OPEN": "CLOSING_NODE"
    }
  };

  // Main view of our tree nodes, e.g. prefixes. Handles all main concerns like
  // toggling them open/closed and so on.
  var NodeView = Marionette.LayoutView.extend({
    tagName: "li",
    className: "prefix-tree-item prefix-tree-item-closed",
    template: "#prefix-tree-node",

    regions: {
      usage_graph: ".prefix-graphs:first",
      children: ".prefix-tree-children-container",
      available_subnets: ".prefix-tree-available-subnets:first"
    },

    events: {
      "click a.prefix-tree-item-title:first": "toggleOpen",
      "touchstart a.prefix-tree-item-title:first": "toggleOpen"
    },

    behaviors: {
      StateMachine: {
        states: nodeViewStates,
        handlers: {
          "LOADING_STATS": "loadingStats",
          "SHOWING_CHILDREN": "showingChildren",
          "OPENING_NODE": "openingNode",
          "CLOSING_NODE": "closingNode",
          "OPEN_NODE": "openNode"
        }
      }
    },

    onBeforeDestroy: function() {
      // Remove marker class for open node in tree, so new results (upon
      // searching/filtering) aren't blurred.
      this.$el.parent().removeClass("prefix-tree-open");
      if (this.ch) {
        this.ch.vent.off("open_node");
      }
    },

    initialize: function() {
      var self = this;
      var pk = this.model.get("pk");
      // In this case, initialize the node with an unique identifier, so it's
      // easier to track down edge cases for certain prefixes.
      this.debug = debug.new("views:nodeview:" + pk);
      this.debug("Mounted node #", pk);
      this.fsm.onChange(function(nextState) {
        self.debug("Moving into state", nextState);
      });
      var self = this;
      this.ch = Backbone.Wreqr.radio.channel("global");
      this.ch.vent.on("open_node", function(__pk) {
        if (__pk !== pk) {
          return;
        }
        self.fsm.step("TOGGLE_OPEN");
      });
    },

    // STATE MACHINE START

    // When the node has been opened by the user.
    openNode: function(self) {
      self.fsm.step("SHOW_CHILDREN");
    },

    // Handle everything related to opening and displaying the node.
    openingNode: function(self) {
      self.debug("Opening node", self.model.get("pk"));
      self.fsm.step("OPENED_NODE");
      // mark parent tree as having open node
      self.$el.addClass("prefix-tree-item-open");
      self.$el.removeClass("prefix-tree-item-closed");
      self.trigger("open_node");
      // open the node itself
      var content = self.$el.find(".prefix-tree-item-content:first");
      var title = self.$el.find(".prefix-tree-item-title:first");
      content.slideToggle(200);//.toggleClass("prefix-item-open");
      title.addClass("prefix-item-open");
      // Mount subnet allocator
      var prefix = self.model.get("prefix");
      self.showChildView("available_subnets", new Views.SubnetAllocator({
        prefix: prefix
      }));
    },

    closingNode: function(self) {
      self.debug("Closing node", self.model.get("pk"));
      self.fsm.step("CLOSED_NODE");
      // TODO replace this with message passing and parent.mode.("hasopenchildren")
      self.$el.removeClass("prefix-tree-item-open");
      self.$el.addClass("prefix-tree-item-closed");
      self.trigger("close_node");
      // close the node itself
      var content = self.$el.find(".prefix-tree-item-content:first");
      var title = self.$el.find(".prefix-tree-item-title:first");
      content.slideToggle(200);//.toggleClass("prefix-item-open");
      title.removeClass("prefix-item-open");
    },

    // We're currently trying to fetch some usage stats (see 'views/usage.js').
    // In this case, the event also sends some data, namely the usage stats
    // themselves.
    loadingStats: function(self, statMap) {
      self.model.set("usage", statMap.usage);
      self.model.set("allocated", statMap.allocated);
      self.debug("Updated stats of prefix #", self.model.get("pk"), "to", statMap);
      self.fsm.step("DONE_LOADING_STATS");
    },

    // We defer drawing children to return a shallow tree faster to the user
    // TODO: Look into bug where the debug function is registered multiple times
    // when sorting. Probably not killing all the child nodes or something
    showingChildren: function(self) {
      if (!self.model.hasChildren()) {
        return;
      }
      self.debug("Rendering children for", self.model.get("pk"));
      var children = self.model.children;
      var model = new Models.Tree();
      model.set('parent', self.model.get('prefix'));
      var payload = {
        model: model,
        collection: children
      };
      self.showChildView("children", new TreeView(payload));
    },

    // STATE MACHINE END

    toggleOpen: function(evt) {
      if (_.isObject(evt)) {
        evt.preventDefault();
      }
      this.fsm.step("TOGGLE_OPEN");
    },

    // Defer drawing usage to speed up rendering
    onAttach: function() {
      // Don't get usage for fake nodes, e.g. usually RFC1918. TODO: Maybe
      // rewrite API to use prefix instead of PK? Seems more sensible.
      if (this.model.get("is_mock_node", true)) {
        return;
      }
      var self = this;
      var utilization = this.model.get("utilization");
      var pk = this.model.get("pk");
      var net_type = this.model.get("net_type");
      this.showChildView("usage_graph", new Views.UsageGraph({
        fsm: self.fsm,
        model: new Models.Usage({ pk: pk, net_type: net_type }),
        utilization: utilization
      }));
    }
  });

  // Container for prefix nodes, nested or otherwise
  var TreeView = Marionette.CompositeView.extend({
    debug: debug.new("views:treeview"),
    template: "#prefix-children",
    childView: NodeView,
    childViewContainer: ".prefix-tree-children",
    reorderOnSort: true,

    childEvents: {
      "open_node": "incrementOpenNodes",
      "close_node": "decrementOpenNodes"
    },

    events: {
      "change .sort-by": "onSortBy",
      "click .close-all": "resetOpenNodes"
    },

    // Functions used to determine the sorting order of the tree's children.
    comparators: {
      prefix: null,
      vlan: function(model) {
        return -1.0 * model.get("vlan_number", 0);
      },
      usage: function(model) {
        return -1.0 * model.get("usage", 0);
      },
      allocated: function(model) {
        return -1.0 * model.get("allocated", 0);
      }
    },

    initialize: function() {
      var self = this;
      // Reset sort to default when we fetch new tree data
      this.collection.bind("sync", this.resetSort.bind(this, this));
      // Default state: No nodes are open
      this.$el.addClass("has_no_open_nodes");
    },

    // Handle open nodes, i.e. blur all non-open nodes if one or more nodes are open
    incrementOpenNodes: function(evt) {
      this.updateOpenNodes(1);
    },
    decrementOpenNodes: function(evt) {
      this.updateOpenNodes(-1);
    },
    updateOpenNodes: function(delta) {
      var currentCount = this.model.get("open_nodes");
      var newCount = currentCount + delta;
      this.model.set("open_nodes", newCount);
      this.debug("Current open nodes", newCount);
      if (newCount > 0) {
        this.$el.addClass("has_open_nodes");
        this.$el.removeClass("has_no_open_nodes");
      } else {
        this.$el.addClass("has_no_open_nodes");
        this.$el.removeClass("has_open_nodes");
      }
    },
    resetOpenNodes: function() {
      this.debug("Resetting number of open nodes to 0");
      // close all open nodes via hard reset, just to be safe
      this.render();
      // update model
      this.model.set("open_nodes", 0);
    },

    // Revert to default order (e.g. order returned by API, where the nodes are
    // sorted by their prefixes).
    resetSort: function() {
      this.model.set("currentComparator", null);
      this.resetOpenNodes();
      this.render();
    },

    // Force the tree to resort itself
    resort: function(self) {
      if (_.isUndefined(self.model)) {
        return;
      }
      // all nodes will be closed, so reset counter
      self.resetOpenNodes();
      var currentComparator = self.model.get("currentComparator");
      var comparatorFn = self.comparators[currentComparator] || null;
      self.viewComparator = comparatorFn;
      self.render();
    },

    // Utility function to show any children of the prefix node in a different
    // order than insertion (e.g. the result returned by the API). This allows
    // us to prevent a different view without proxying the underlying collection
    // (for example, it is rather cumbersome to cache the original object to
    // revert to insertion order if desired by the user).
    onSortBy: function(evt) {
      evt.preventDefault();
      evt.stopPropagation();
      var value = this.$(evt.target).val();
      this.debug("Ordering children by", value);
      this.model.set("currentComparator", value);
      this.resort(this);
    }

  });

  exports.RootView = RootView;
  exports.NodeView = NodeView;

});

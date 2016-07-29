define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Views = require("src/ipam/views/index");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");


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

  // Base of tree
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

    /* Refetch collection */
    refetch: function() {
      // Cancel existing fetches to avoid happy mistakes
      if (typeof this.xhr !== "undefined") {
        this.debug("Aborted previous fetch!");
        this.xhr.abort();
      }
      // Keep a pointer to the fetch object, for tracking all fetches
      this.xhr = this.collection.fetch({reset: true});
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

      // Handle updated params
      globalCh.vent.on("search:update", function(params) {
        self.debug("Got new search params", params);
        self.collection.queryParams = params;
        self.refetch();
      });
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

    onBeforeShow: function() {
      this.showChildView("tree", new TreeView({
        model: new Models.Tree(),
        collection: this.collection
      }));
    },

    onRender: function() {
      if (this.isFetching()) {
        flash.fetch();
      }
      // TODO: show load/fetch messages
      if (this.isEmpty()) {
        var searchParams = this.collection.queryParams.search;
        flash.noResult(searchParams);
      } else {
        flash.reset();
      }
    }

  });

  // TODO: Fetch available subnets, see available_subnets in prefix_tree.py
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


  var NodeView = Marionette.LayoutView.extend({
    tagName: "li",
    className: "prefix-tree-item",
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

    initialize: function() {
      var self = this;
      var pk = this.model.get("pk");
      this.debug = debug.new("views:nodeview:" + pk);
      this.debug("Mounted node #", pk);
      this.fsm.onChange(function(nextState) {
        self.debug("Moving into state", nextState);
      });
    },

    openNode: function(self) {
      self.fsm.step("SHOW_CHILDREN");
    },

    openingNode: function(self) {
      self.debug("Opening node", self.model.get("pk"));
      self.fsm.step("OPENED_NODE");
      self.toggle();
    },

    closingNode: function(self) {
      self.debug("Closing node", self.model.get("pk"));
      self.fsm.step("CLOSED_NODE");
      self.toggle();
    },

    loadingStats: function(self, statMap) {
      self.model.set("usage", statMap.usage);
      self.model.set("allocated", statMap.allocated);
      self.debug("Updated stats of prefix #", self.model.get("pk"), "to", statMap);
      self.fsm.step("DONE_LOADING_STATS");
    },

    toggleOpen: function(evt) {
      if (_.isObject(evt)) {
        evt.preventDefault();
      }
      this.fsm.step("TOGGLE_OPEN");
    },

    // Hide/show element
    toggle: function() {
      // open content
      var content = this.$el.find(".prefix-tree-item-content:first");
      var title = this.$el.find(".prefix-tree-item-title:first");
      content.slideToggle(200);//.toggleClass("prefix-item-open");
      title.toggleClass("prefix-item-open");
      // mount subnet treemap
      var prefix = this.model.get("prefix");
      this.showChildView("available_subnets", new Views.SubnetAllocator({
        prefix: prefix
      }));
      this.debug("Toggle " + this.model.get("pk"));
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
      var payload = {
        model: new Models.Tree(),
        collection: children
      };
      self.showChildView("children", new TreeView(payload));
      //self.fsm.step("DONE_SHOWING_CHILDREN");
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
      this.showChildView("usage_graph", new Views.UsageGraph({
        fsm: self.fsm,
        model: new Models.Usage({ pk: pk }),
        utilization: utilization
      }));
    }
  });

  // Dumb container for prefix nodes, nested or otherwise
  var TreeView = Marionette.CompositeView.extend({
    debug: debug.new("views:treeview"),
    template: "#prefix-children",
    childView: NodeView,
    childViewContainer: ".prefix-tree-children",
    reorderOnSort: true,

    // Comparator stuff
    comparators: {
      prefix: null,
      vlan: function(model) {
        return -1.0 * model.get("vlan-number", 0);
      },
      usage: function(model) {
        return -1.0 * model.get("usage", 0);
      },
      allocated: function(model) {
        return -1.0 * model.get("allocated", 0);
      }
    },

    events: {
      "click .sort-by": "onSortBy"
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
      var comparatorFn = this.comparators[value] || null;
      this.viewComparator = comparatorFn;
      this.render();
    }

  });

  exports.RootView = RootView;
  exports.NodeView = NodeView;

});

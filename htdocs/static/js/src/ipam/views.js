define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Foundation = require("libs/foundation.min");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var viz = require("src/ipam/viz");

  // Global communication channel with main app
  var globalCh = Backbone.Wreqr.radio.channel("global");
  var nodeCh = Backbone.Wreqr.radio.channel("nodes");

  // Utility object for flashing
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

  // Logging factory
  var debug = require("src/ipam/util").ipam_debug;

  // Subview for available subnets for the current prefix/scope
  var AvailableSubnetsView = Marionette.ItemView.extend({
    debug: debug.new("views:available_subnets"),
    template: "#prefix-available-subnets",
    events: {
      "click .fetch-subnets": "fetch",
      "click .hide-subnets": "hide"
    },

    modelEvents: {
      "change": "render"
    },

    initialize: function(opts) {
      this.model = new Models.AvailableSubnets({
        queryParams: {
          prefix: opts.prefix
        }
      });
      this.debug("Mounted subnet component for " + opts.prefix);
    },

    hide: function(evt) {
      evt.preventDefault();
      evt.stopPropagation();
      this.$el.find(".subnets:first").hide();
      this.model.set("hide", true);
    },

    fetch: function(evt) {
      evt.preventDefault();
      evt.stopPropagation();
      this.refetch();
    },

    refetch: function() {
      var prefix = this.model.get("queryParams").prefix;
      this.debug("Trying to get subnets for " + prefix);
      // cache xhr object
      this.xhr = this.model.fetch({reset: true});
      this.xhr.done(this.render);
    }
  });

  // Control form for tree
  var ControlView = Marionette.LayoutView.extend({
    debug: debug.new("views:control"),
    template: "#prefix-control-form",

    regions: {
      "advanced": ".prefix-control-form-advanced"
    },

    events: {
      "input .prefix-tree-query": "updateSearch",
      "change .search-param": "updateSearch",
      "change .search-flag": "updateSearch",
      "change .net_types": "updateNetTypes",
      "click .toggleAdvanced": "toggleAdvanced"
    },

    updateNetTypes: function(evt) {
      var elem = $(evt.target);
      console.log(elem.val());
    },

    // Activate advanced form
    toggleAdvanced: function() {
      var advancedSearch = this.model.get("advancedSearch");
      this.debug("Displaying advanced search => " + !advancedSearch);
      this.model.set("advancedSearch", !advancedSearch);
      this.render();
      // make datetimepicker detect forms
      $(".datetimepicker").datetimepicker({
        'dateFormat': 'yy-mm-dd',
        'timeFormat': 'HH:mm'
      });
    },

    onRender: function() {
      var advancedSearch = this.model.get("advancedSearch");
      var self = this;
      if (advancedSearch) {
        this.showChildView("advanced", new ControlAdvancedView({
          model: self.model
        }));
      }
      // Detect select2 inputs
      this.$el.find(".select2").select2();
    },

    _updateSearch: function() {
      var params = {};
      // handle check boxes
      var checked = this.$el.find("input.search-flag:checked");
      checked.each(function() {
        var elem = $(this);
        var param = elem.attr("name");
        var param_field = params[param] || [];
        param_field.push(elem.val());
        params[param] = param_field;
      });

      // Dynamically collect all inputs marked using".search-param". These
      // fields are exclusively non-nested, hence no need to collect them into
      // an array (unlike checkboxes)
      var search_params = this.$el.find(".search-param");
      search_params.each(function() {
        var elem = $(this);
        var param = elem.attr("name");
        var value = elem.val();
        if (!value) {
          return;
        }
        params[param] = value;
      });

      // handle search string
      params["search"] = this.$el.find("#prefix-tree-query").val();
      // update globally
      this.model.set("queryParams", params);
      globalCh.vent.trigger("search:update", params);
    },

    initialize: function() {
      this.updateSearch = _.throttle(this._updateSearch, 1000);
    }

  });

  var ControlAdvancedView = Marionette.ItemView.extend({
    template: "#prefix-control-form-advanced"
  });

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
  var NodeView = Marionette.LayoutView.extend({
    debug: debug.new("views:nodeview"),
    tagName: "li",
    className: "prefix-tree-item",
    template: "#prefix-tree-node",

    regions: {
      usage_graph: ".prefix-graphs:first",
      children: ".prefix-tree-children-container",
      available_subnets: ".prefix-tree-available-subnets:first"
    },

    events: {
      "click a.prefix-tree-item-title": "toggleOpen",
      "touchstart a.prefix-tree-item-title": "toggleOpen"
    },

    initialize: function() {
      var self = this;
      var pk = this.model.get("pk");
      this.debug("Mounted node #", pk);
      this.mailbox = Backbone.Wreqr.radio.channel("node" + pk);
      // Using 'once' here instead of 'one' to avoid attaching multiple
      // persistent handlers, which leaks memory.
      this.mailbox.vent.once("update:stats", function(stats) {
        self.model.set("usage", stats.usage);
        self.model.set("allocated", stats.allocated);
        self.debug("Updated stats of prefix #", pk, "to", stats);
      });
    },

    // Hide/show element
    toggleOpen: function(evt) {
      // avoid bubbling up to parent, as we're dealing with nested views
      evt.preventDefault();
      evt.stopPropagation();
      // open content
      var content = this.$el.find(".prefix-tree-item-content:first");
      var title = this.$el.find(".prefix-tree-item-title:first");
      content.slideToggle(200);//.toggleClass("prefix-item-open");
      title.toggleClass("prefix-item-open");
      // deferred rendering of children
      if (!this.model.hasShownChildren() && this.model.hasChildren()) {
        this.showChildren();
      }
      this.debug("Toggle " + this.model.get("pk"));
    },

    // We defer drawing children to return a shallow tree faster to the user
    // TODO: Look into bug where the debug function is registered multiple times
    // when sorting. Probably not killing all the child nodes or something
    showChildren: function() {
      this.debug("Rendering children for", this.model.get("pk"));
      var self = this;
      var children = this.model.children;
      var payload = {
        model: new Models.Tree(),
        collection: children
      };
      this.showChildView("children", new TreeView(payload));
      this.model.set("hasShownChildren", true);
    },

    // Defer drawing usage to speed up rendering
    onAttach: function() {
      // Don't get usage for fake nodes, e.g. usually RFC1918. TODO: Maybe
      // rewrite API to use prefix instead of PK? Seems more sensible.
      if (this.model.get("is_mock_node", true)) {
        return;
      }
      var utilization = this.model.get("utilization");
      var pk = this.model.get("pk");
      var mailbox = this.mailbox;
      this.showChildView("usage_graph", new UsageGraph({
        mailbox: mailbox,
        model: new Models.Usage({ pk: pk }),
        utilization: utilization
      }));
    },

    onBeforeShow: function() {
      // Mount subnet component
      var prefix = this.model.get("prefix");
      this.showChildView("available_subnets", new AvailableSubnetsView({
        prefix: prefix
      }));
    }

  });

  /* Dumb view for mounting usage graph */
  var UsageGraph = Marionette.ItemView.extend({
    template: "#prefix-graphs",
    debug: debug.new("views:usagegraph"),
    // mock - for catching dhcp treshold change in parent?
    triggers: {
      "click svg": "update:dhcp_treshold"
    },

    initialize: function(opts) {
      this.debug("Mounting usage view.");
      // Fetch usage data, then draw
      this.model.fetch().done(this.onReceive.bind(this, this));
      this.parent = opts.mailbox.vent;
    },

    // TODO: Draw how much of the prefix has been allocated to others
    onReceive: function() {
      this.debug("Received usage data");
      var usage = this.model.get("usage");
      var allocated = this.model.get("allocated");
      // Bubble up captured value to parent model
      this.parent.trigger("update:stats", {
        usage: usage,
        allocated: allocated
      });
      // don't draw unless we have some usage
      if (typeof usage === "undefined" || typeof allocated === "undefined") {
        return;
      }

      var usageElem = this.$el.find(".usage-graph:first");
      var usageTmpl = _.template("<span>Usage: <%= percent %> %</span>");
      usageElem.append(usageTmpl({percent: (usage * 100).toFixed(2)}));
      viz.usageChart({
        mountElem: usageElem.get(0),
        width: 100,
        height: 10,
        data: [{
          fill: "lightsteelblue",
          name: "Available",
          value: 1.0 - usage
        },{
          fill: "white",
          name: "Used",
          value: usage
        }]
      });

      var allocationElem = this.$el.find(".allocation-graph:first");
      var allocationTmpl = _.template("<span>Allocated: <%= percent %> %</span>");
      allocationElem.append(allocationTmpl({percent: (allocated * 100).toFixed(2)}));
      viz.usageChart({
        mountElem: allocationElem.get(0),
        width: 100,
        height: 10,
        data: [{
          fill: "lightsteelblue",
          name: "Available",
          value: 1.0 - allocated
        },{
          fill: "white",
          name: "Allocated",
          value: allocated
        }]
      });
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

  module.exports = {
    "NodeView": NodeView,
    "ControlView": ControlView,
    "RootView": RootView
  };

});

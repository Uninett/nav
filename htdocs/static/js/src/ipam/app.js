// MVC for prefix tree, probably forms etc.

define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Foundation = require("libs/foundation.min");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var viz = require("src/ipam/viz");
  var util = require("src/ipam/util");

  // == MODELS/COLLECTIONS

  var PrefixNode = Backbone.Model.extend({
    defaults: {
      description: "",
      "organization": "",
      "pk": null,
      start: new Date().toISOString(),
      end: null
    },

    // Check if a node or its children matches a filter TODO: Reconsider this.
    // Probably not a smart idea. Rather, filter the list of prefix nodes
    // directly and then construct a new view of the resulting collection.
    matches: function(filter) {
      if (!filter || _.isUndefined(filter)) {
        return true;
      }
      return true;
    },

    // TODO: validate: function() {}

    initialize: function() {
      // Recursively instantiate any children
      var children = this.get("children");
      if (children) {
        this.children = new PrefixNodes(children);
        this.unset("children");
      }
    }
  });

  // Container for trees (and subtrees)
  var PrefixNodes = Backbone.Collection.extend({
    model: PrefixNode,
    baseUrl: "ipam/api",
    // Default query params
    queryParams: {
      type: ["ipv4", "ipv6"]
    },

    initialize: function(models, args) {
      var self = this;
      this.url = function() {
        var params = decodeURIComponent($.param(self.queryParams, true));
        return "/ipam/api/?" + params;
      };
      this.parse = function(resp) {
        console.log("Received response from " + this.url());
        console.log(resp);
        return resp;
      };
    }
  });

  // == VIEWS

  // Main node view. Recursively renders any children of that node as well.
  var PrefixNodeView = Marionette.CompositeView.extend({
    tagName: "li",
    className: "accordion-navigation prefix-tree-item",
    template: "#prefix-tree-node",

    // TODO: Add handlers for getting the usage stats?
    events: {
      "click .filter": "filter"
    },

    initialize: function() {
      this.collection = this.model.children;
    },

    // Things to do after initial render
    onRender: function() {
      // Mount usage graph
      if (this.model.get("utilization")) {
        var utilization = this.model.get("utilization");
        var usageElem = this.$el.find(".prefix-usage-graph");
        var template = _.template("<span>Usage: <%= percent %> %</span>");
        usageElem.html(template({percent: (utilization * 100).toFixed(2)}));

        viz.usageChart({
          mountElem: usageElem.get(0),
          width: 100,
          height: 5,
          data: [{
            fill: "lightsteelblue",
            name: "Used",
            value: 1.0 - utilization
          },{
            fill: "steelblue",
            name: "Available",
            value: utilization
          }]
        });
      }
    },

    // Filter children of node
    filter: function(child) {
      return true;
    },

    // Append to nearest active container, e.g. current parent
    attachHtml: function(collectionView, childView) {
      collectionView.$(".prefix-tree-children:first").append(childView.el);
    }

  });

  // Dumb container for whole tree. Note: this.fetchXhr contains the reference
  // to the (previous) fetch, which might be used to abort it if needed.
  var TreeRoot = Marionette.CompositeView.extend({
    template: "#prefix-list",
    childViewContainer: ".prefix-tree-children",
    childView: PrefixNodeView,

    events: {
      "input .prefix-tree-query": "search",
      "change .prefix-types": "updateTypes"
    },

    // Check if we have an empty tree
    isEmpty: function() {
      return !this.collection || this.collection.length === 0;
    },

    /* Refetch collection */
    refetch: function() {
      // Cancel existing fetches to avoid happy mistakes
      if (typeof this.fetchXhr !== "undefined") {
        console.log("Aborted previous fetch!");
        this.fetchXhr.abort();
      }
      // Keep a pointer to the fetch object, for tracking all fetches
      this.fetchXhr = this.collection.fetch({reset: true});
      this.flash("alert-box", "Fetching...");
    },

    // Grab address types and update query params
    updateTypes: function() {
      var types = [];
      $("input[name='types[]']:checked").each(function (){
        var elem = $(this);
        types.push(elem.val());
      });
      console.log("Only querying for prefixes of the following families:");
      console.log(types);
      this.collection.queryParams["type"] = types;
      this.refetch();
    },

    // TODO: Cancel any existing fetches
    _search: function() {
      // Grab free text search
      var val = $(".prefix-tree-query").val();
      // construct search params
      this.collection.queryParams.search = val;
      this.refetch();
    },

    initialize: function() {
      // Wrap in a throttle to avoid sad XHR requests
      this.search = _.throttle(this._search, 1000);
      // Don't mess with the ordering
      this.sort = false;
      // Don't render before fetch of collection returns
      this.collection = new PrefixNodes();
      this.fetchXhr = this.collection.fetch({reset: true});
      // Handle reset events, e.g. when a fetch is done
      this.collection.bind("reset", this.onRender, this);
      this.collection.bind("fetch", this.onRender, this);
    },

    // Flash a simple message to the user TODO: Add classes to fetch messages,
    // so they can easily be styled using SASS.
    flash: function(klass, html) {
      var template = _.template("<div class='<%= klass %>'><%= content %></div>");
      var content = template({
        klass: klass,
        content: html
      });
      console.log("Flashed a message");
      var flashElem = this.$el.find(".prefix-tree-flash");
      flashElem.html(content);
    },

    resetFlash: function() {
      var elem = this.$el.find(".prefix-tree-flash");
      elem.html(null);
    },

    isFetching: function() {
      if (typeof this.fetchXhr === "undefined") {
        return false;
      }
      switch (this.fetchXhr.readyState) {
      case 1:
      case 2:
      case 3:
        return true;
      default:
        return false;
      }
    },

    onRender: function() {
      if (this.isFetching()) {
        return this.flash("alert-box", "Fetching...");
      }
      // TODO: show load/fetch messages
      if (this.isEmpty()) {
        var template = _.template("No results for <strong>'<%- query %>'</strong>");
        var searchParams = this.collection.queryParams.search;
        return this.flash("alert-box alert with-icon", template({query: searchParams }));
      } else {
        return this.resetFlash();
      }
    },

    filterStuff: function() {
      // handle filtering, trigger new fetch with reset: true etc
    }
  });

  // == APP LIFECYCLE MANAGEMENT

  var App = new Marionette.Application();

  // TODO: Create regions for forms, main statistics (overused/underused networks)
  App.on("before:start", function() {
    App.addRegions({
      main: "#prefix-tree"
    });
  });

  App.on("start", function() {
    console.log("Trying to render prefix tree...");

    var treeView = new TreeRoot({
      // TODO: Insert any tree state here
      model: new (Backbone.Model.extend({
        defaults: {
          filter: "*"
        }}))
    });

    this.main.show(treeView);

    console.log("Didn't crash. Great success!");

    // Must be called for Foundation to notice the generated accordions
    $(document).foundation({
      accordion: {
        multi_expand: true
      }
    });
  });

  module.exports = App;

});

// MVC for prefix tree, probably forms etc.

define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Foundation = require("libs/foundation.min");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

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
    model: PrefixNode
  });

  // == VIEWS

  // Main node view. Recursively renders any children of that node as well.
  var PrefixNodeView = Marionette.CompositeView.extend({
    tagName: "li",
    className: "accordion-navigation scope-tree-item",
    template: "#scope-tree-node",

    // TODO: Add handlers for getting the usage stats?
    events: {
      "click .filter": "filter"
    },

    initialize: function() {
      this.collection = this.model.children;
    },

    // Filter children of node
    filter: function(child) {
      return true;
      var filter = $("#scope-filter").val();
      console.log("Filter: " + filter);
      var res = child.matches(filter);
      if (res) {
        console.log("filtering away");
        console.log(child.model);
      }
      return res;
    },

    // Append to nearest active container, e.g. current parent
    attachHtml: function(collectionView, childView) {
      collectionView.$(".scope-tree-children:first").append(childView.el);
    }

  });

  // Dumb container for whole tree
  var TreeRoot = Marionette.CompositeView.extend({
    template: "#scope-list",
    childViewContainer: ".scope-tree-children",
    childView: PrefixNodeView
  });

  // == APP LIFECYCLE MANAGEMENT

  var App = new Marionette.Application();

  // TODO: Create regions for forms, main statistics (overused/underused networks)
  App.on("before:start", function() {
    App.addRegions({
      main: "#scope-tree"
    });
  });

  App.on("start", function() {
    if (typeof PREFIX_TREE === "undefined" || PREFIX_TREE === null) {
      console.log("Couldn't find prefix tree.");
      return;
    }
    console.log("Found prefix tree! Trying to render...");
    var treeView = new TreeRoot({
      collection: new PrefixNodes(PREFIX_TREE.children),
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

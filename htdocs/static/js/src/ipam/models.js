define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var debug = require("src/ipam/util").debug;

  var PrefixNode = Backbone.Model.extend({
    debug: debug("models:prefixnode"),
    defaults: {
      description: "",
      "organization": "",
      "pk": null,
      start: new Date().toISOString(),
      end: null,
      hasShownChildren: false
    },

    hasShownChildren: function() {
      return this.get("hasShownChildren");
    },

    hasChildren: function() {
      var children = this.get("children") || this.children.models;
      if (_.isUndefined(children) || _.isEmpty(children)) {
        return false;
      }
      return true;
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
    debug: debug("models:prefixnodes"),
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
        this.debug("Received response from " + this.url(), resp);
        return resp;
      };
    }
  });

  // Calls to available subnets API
  var AvailableSubnets = Backbone.Model.extend({
    debug: debug("models:availablesubnets"),
    baseUrl: "/ipam/api/find?",

    defaults: {
      available_subnets: [],
      hide: true,
      queryParams: {
        prefix: "10.0.0.0/16"
      }
    },

    initialize: function() {
      var self = this;
      this.url = function() {
        var queryParams = this.get("queryParams");
        var params = decodeURIComponent($.param(queryParams, true));
        return this.baseUrl + params;
      };
      this.parse = function(resp) {
        this.debug("Received response from " + this.url(), resp);
        this.set("hide", false);
        return resp;
      };
    }
  });

  // State/model for control form subview
  var Control = Backbone.Model.extend({
    defaults: {
      advancedSearch: false,
      queryParams: {
        type: [],
        search: null,
        net_type: [],
        timestart: null,
        timeend: null,
        organization: null,
        usage: null,
        vlan: null
      }
    }
  });

  module.exports = {
    "PrefixNodes": PrefixNodes,
    "PrefixNode": PrefixNode,
    "AvailableSubnets": AvailableSubnets,
    "Control": Control
  };

});

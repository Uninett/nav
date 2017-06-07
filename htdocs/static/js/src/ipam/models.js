define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var debug = require("src/ipam/util").ipam_debug;
  var FSM = require("src/ipam/util").FSM;

  var PrefixNode = Backbone.Model.extend({
    debug: debug.new("models:prefixnode"),
    defaults: {
      // plaintext description of VLAN
      description: "",
      // VLAN organization
      "organization": "",
      // usage of VLAN
      "vlan_usage": null,
      // Primary key (in DB)
      "pk": null,
      start: new Date().toISOString(),
      end: null,
      // Percentwise usage (active_addr/max_addr),
      usage: 0.0,
      // Percent of prefix allocated to other scopes/reservations
      allocated: 0.0
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
    debug: debug.new("models:prefixnodes"),
    model: PrefixNode,
    baseUrl: "/ipam/api/?",
    // Default query params
    queryParams: null,

    initialize: function(models, args) {
      var self = this;
      this.url = function() {
        var params = decodeURIComponent($.param(self.queryParams, true));
        return self.baseUrl + params;
      };
      this.parse = function(resp) {
        this.debug("Received response from " + this.url(), resp);
        return resp;
      };
    }
  });

  // Calls to the total usage API
  var Usage = Backbone.Model.extend({
    debug: debug.new("models:usage"),
    urlTemplate: _.template("/ipam/api/<%= pk %>/usage"),
    defaults: {
      pk: null,
      usage: 0,
      queryParams: {}
    },

    initialize: function() {
      var self = this;
      this.url = function() {
        var queryParams = self.get("queryParams");
        var pk = self.get("pk");
        var params = decodeURIComponent($.param(queryParams, true));
        var baseUrl = self.urlTemplate({ pk: pk });
        return baseUrl + params;
      };
      this.parse = function(resp) {
        this.debug("Received response from " + this.url(), resp);
        return resp;
      };
    }

  });

  // Calls to available subnets API
  var AvailableSubnets = Backbone.Model.extend({
    debug: debug.new("models:availablesubnets"),
    urlTemplate: _.template("/ipam/api/?net_type=all&within=<%= prefix %>&show_all=True"),

    defaults: {
      state: "Initial state",
      // Currently focused node in treemap
      focused_node: {},
      raw_data: {},
      data: [],
      hide: true,
      queryParams: {
        prefix: "10.0.0.0/16"
      }
    },

    initialize: function() {
      var self = this;
      this.url = function() {
        var queryParams = this.get("queryParams");
        return self.urlTemplate(queryParams);
      };
      this.parse = function(resp) {
        this.debug("Received response from " + this.url(), resp);
        this.set("hide", false);
        return { raw_data: resp };
      };
    }
  });

  // State/model for control form subview
  var Control = Backbone.Model.extend({
    defaults: {
      state: "Initial state",
      advancedSearch: false,
      queryParams: {
        ip: null,
        type: ["ipv4", "ipv6", "rfc1918"],
        net_type: ["scope"],
        search: null,
        timestart: null,
        timeend: null,
        organization: null,
        usage: null,
        vlan: null,
        description: null,
        prefix: null
      }
    }
  });

  var Tree = Backbone.Model.extend({
    defaults: {
      open_nodes: 0,
      currentComparator: "prefix",
      parent: null
    }
  });

  module.exports = {
    "PrefixNodes": PrefixNodes,
    "PrefixNode": PrefixNode,
    "AvailableSubnets": AvailableSubnets,
    "Control": Control,
    "Usage": Usage,
    "Tree": Tree
  };

});

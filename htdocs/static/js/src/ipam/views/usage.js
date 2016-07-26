define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");

  /* Dumb view for mounting usage graph */
  var SubnetAllocator = Marionette.ItemView.extend({
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
      Viz.usageChart({
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
      Viz.usageChart({
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

  module.exports = SubnetAllocator;

});

define(function(require, exports, module) {
  const _ = require("libs/underscore");
  require("backbone");
  const Marionette = require("marionette");
  const Radio = require("backbone.radio");

  require("src/ipam/models");
  const Viz = require("src/ipam/viz");

  const debug = require("src/ipam/util").ipam_debug;
  Radio.channel("global");

  // Responsible for fetching and display usage/allocation stats. Also
  // propagates these values to the parent.
  const SubnetAllocator = Marionette.View.extend({
    template: "#prefix-graphs",
    debug: debug.new("views:usagegraph"),
    // mock - for catching dhcp treshold change in parent?
    triggers: {
      "click svg": "update:dhcp_treshold"
    },

    initialize: function(opts) {
      this.fsm = opts.fsm;
      this.debug("Mounting usage view.");
      // Fetch usage data, then draw
      this.fsm.step("FETCH_STATS");
      this.xhr = this.model.fetch();
      this.xhr.done(this.onReceive.bind(this, this));
    },

    onBeforeDestroy: function() {
      // Kill pending fetches upon destroying this component
      if (!_.isUndefined(this.xhr)) {
        this.xhr.abort();
      }
    },

    // Handle a successful fetch
    onReceive: function() {
      this.debug("Received usage data");
      const usage = this.model.get("usage");
      const allocated = this.model.get("allocated");
      // Bubble up captured value to parent model
      this.fsm.step("DONE_FETCHING_STATS", {
        usage: usage,
        allocated: allocated
      });
      // don't draw unless we have some usage
      if (typeof usage === "undefined" || typeof allocated === "undefined") {
        return;
      }
      // Don't show allocation stats for things that aren't scopes, as this
      // makes no sense
      if (this.model.get("net_type") === "scope") {
        const allocationElem = this.$el.find(".allocation-graph:first");
        const allocationTmpl = _.template("<span title='Ratio of the scope that has been allocated to subnets'>Allocated: <%= percent %> %</span>");
        allocationElem.append(allocationTmpl({percent: (allocated * 100).toFixed(2)}));
        Viz.usageChart({
          mountElem: allocationElem.get(0),
          width: 100,
          height: 10,
          data: [{
            fill: "white",
            name: "Available",
            value: 1.0 - allocated
          }, {
            fill: "lightsteelblue",
            name: "Allocated",
            value: allocated
          }]
        });
      }

      const usageElem = this.$el.find(".usage-graph:first");
      const usageTmpl = _.template("<span title='Based on current active IP addresses'>Current usage: <%= percent %> %</span>");
      usageElem.append(usageTmpl({percent: (usage * 100).toFixed(2)}));
      Viz.usageChart({
        mountElem: usageElem.get(0),
        width: 100,
        height: 10,
        data: [{
          fill: "white",
          name: "Available",
          value: 1.0 - usage
        }, {
          fill: "lightsteelblue",
          name: "Used",
          value: usage
        }]
      });
    }
  });

  module.exports = SubnetAllocator;

});

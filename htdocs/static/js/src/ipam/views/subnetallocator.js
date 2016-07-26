define(function(require, exports, module) {

  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");
  var d3v4 = require("d3v4");
  var debug = require("src/ipam/util").ipam_debug.new("views:available_subnets");

  var Models = require("src/ipam/models");
  var Viz = require("src/ipam/viz");

  var AvailableSubnetsView = Marionette.ItemView.extend({
    debug: debug,
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

    // TODO: Need to handle case of no children, e.g. no subnets
    onReceive: function() {
      var target = this.$el.find(".allocation-tree:first").get(0);
      var data = this.model.get("raw_data");
      Viz.allocationMatrix({
        data: { prefix: "*", children: data },
        mountElem: target,
        width: 1024,
        height: 200
      });
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
      this.xhr.done(this.onReceive.bind(this, this));
    }
  });

  module.exports = AvailableSubnetsView;

});

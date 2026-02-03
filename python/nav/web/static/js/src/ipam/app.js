// Main point of entry for the IPAM application itself.

define(function(require, exports, module) {
  const _ = require("libs/underscore");
  require("backbone");
  const Marionette = require("marionette");
  const Radio = require("backbone.radio");

  // Configure Marionette v4 to handle template selectors like "#template-id"
  // (Marionette v2 did this automatically, v4 requires explicit configuration)
  Marionette.setRenderer(function(template, data) {
    if (typeof template === 'function') {
      return template(data);
    }
    if (typeof template === 'string' && template.startsWith('#')) {
      const templateHtml = $(template).html();
      return _.template(templateHtml)(data);
    }
    return template;
  });

  const Models = require("src/ipam/models");
  const Views = require("src/ipam/views/index");

  const util = require("src/ipam/util");

  // == APP SINGLETON
  const App = new Marionette.Application();
  const debug = util.ipam_debug.new("app");

  // Global radio channel for app-wide events (replaces App.vent from Wreqr)
  const globalCh = Radio.channel("global");

  // Create regions (v4 style - regions are created separately)
  const mainRegion = new Marionette.Region({ el: "#prefix-tree" });
  const controlsRegion = new Marionette.Region({ el: "#ipam-controls" });

  // Instantiate application by fetching a tree and drawing stuff
  App.on("start", function() {
    debug("Trying to render prefix tree...");
    mainRegion.show(new Views.RootView({
      collection: new Models.PrefixNodes(),
      childView: Views.NodeView
    }));

    controlsRegion.show(new Views.ControlView({
      model: new Models.Control()
    }));

    debug("Didn't crash. Great success!");
  });

  // Handle flash messages
  const flash_debug = util.ipam_debug.new("flash");
  globalCh.on("flash", function(klass, msg) {
    flash_debug("Flashed a message");
    const template = _.template("<div class='<%= klass %>'><%= content %></div>");
    const content = template({
      klass: klass,
      content: msg
    });
    $("#ipam-flash").html(content);
  });

  globalCh.on("flash:reset", function() {
    flash_debug("Reset flash");
    $("#ipam-flash").html(null);
  });

  // Debug button
  $("#mybtn").on("click", function() {
    globalCh.trigger("fetch:all");
  });

  //util.debugListen("available_subnets");
  //util.ipam_debug.listen("app");
  //util.ipam_debug.listen("models");
  //util.ipam_debug.listen("views");
  //util.ipam_debug.unlisten("models:usage");
  //util.ipam_debug.unlisten("views:available_subnets");
  util.ipam_debug.unlisten("views:nodeview");

  module.exports = App;

});

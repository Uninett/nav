// Main point of entry for the IPAM application itself.

define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  // Import and mount behaviors, so they are available to the views.
  require("src/ipam/views/behaviors")();

  var Models = require("src/ipam/models");
  var Views = require("src/ipam/views/index");

  var util = require("src/ipam/util");

  // == APP SINGLETON
  var App = new Marionette.Application();
  var debug = util.ipam_debug.new("app");

  // == APP LIFECYCLE MANAGEMENT

  // Dynamically mount regions
  App.on("before:start", function() {
    App.addRegions({
      main: "#prefix-tree",
      controls: "#ipam-controls"
    });
  });

  // Instantiate application by fetching a tree and drawing stuff
  App.on("start", function() {
    debug("Trying to render prefix tree...");
    this.main.show(new Views.RootView({
      collection: new Models.PrefixNodes(),
      childView: Views.NodeView
    }));

    this.controls.show(new Views.ControlView({
      model: new Models.Control()
    }));

    debug("Didn't crash. Great success!");
  });

  // Handle flash messages
  var flash_debug = util.ipam_debug.new("flash");
  App.vent.on("flash", function(klass, msg) {
    flash_debug("Flashed a message");
    var template = _.template("<div class='<%= klass %>'><%= content %></div>");
    var content = template({
      klass: klass,
      content: msg
    });
    $("#ipam-flash").html(content);
  });

  App.vent.on("flash:reset", function() {
    flash_debug("Reset flash");
    $("#ipam-flash").html(null);
  });

  // Debug button
  $("#mybtn").on("click", function() {
    App.vent.trigger("fetch:all");
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

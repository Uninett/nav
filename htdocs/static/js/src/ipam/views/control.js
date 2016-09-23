define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");

  var viewStates = {
    "SIMPLE_SEARCH": {
      "WILDCARD_SEARCH": "WILDCARD_SEARCH",
      "TOGGLE_ADVANCED": "ADVANCED_SEARCH"
    },
    "WILDCARD_SEARCH": {},
    "ADVANCED_SEARCH": {
      "TOGGLE_ADVANCED": "SIMPLE_SEARCH"
    }
  };


  // Control form for tree
  module.exports = Marionette.LayoutView.extend({
    debug: debug.new("views:control"),
    template: "#prefix-control-form",

    behaviors: {
      StateMachine: {
        states: viewStates,
        modelField: "state",
        handlers: {
          "ADVANCED_SEARCH": "advancedSearch",
          "SIMPLE_SEARCH": "simpleSearch"
        }
      }
    },

    regions: {
      "advanced": ".prefix-control-form-advanced"
    },

    events: {
      "click .toggleAdvanced": "toggleAdvanced",
      "click .submit-search": "updateSearch",
      "click .submit-reset": "resetSearch",
      "keypress .search-param": "forceSearch"
    },

    // Default parameters for the different kinds of searches
    simpleSearchDefaults: {
      net_type: ["scope"],
      ip: null,
      search: null
    },
    advancedSearchDefaults: {
      type: ["ipv4", "ipv6", "rfc1918"],
      net_type: [],
      organization: null,
      usage: null,
      vlan: null,
      description: null
    },

    // Activate advanced form
    toggleAdvanced: function() {
      this.fsm.step(this.fsm.events.TOGGLE_ADVANCED);
      this.debug("Toggling advanced search");
      this.render();
    },

    simpleSearch: function(self) {
      // Reset model
      self.debug("Reset query params");
      self.model.set("queryParams", self.simpleSearchDefaults);
      self.doSearch();
    },

    advancedSearch: function(self) {
      // Reset model TODO load from localstorage?
      self.debug("Reset query params");
      self.model.set("queryParams", self.advancedSearchDefaults);
    },

    onRender: function() {
      // Detect select2 inputs
      this.$el.find(".select2").select2();
    },

    // If the user triggers a search by hitting enter
    forceSearch: function(evt) {
      if (evt.which === 13 || !evt.which) {
        evt.preventDefault();
        this.updateSearch();
      }
    },

    // Update search parameters and execute a search
    updateSearch: function() {
      this.model.set("queryParams", this.$el.find('form').serializeObject());
      this.doSearch();
    },

    resetSearch: function() {
      // I am a simple man. I click "reset", and reload the page
      location.reload();
    },

    doSearch: function() {
      globalCh.vent.trigger("search:update", this.model.get('queryParams'));
    },

    initialize: function() {
      this.fsm.setState("SIMPLE_SEARCH");
    }

  });

});

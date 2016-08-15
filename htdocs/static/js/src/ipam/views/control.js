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

    // Parse form and get all parameters for search
    _getSearch: function() {
      var params = {};
      // handle check boxes
      var checked = this.$el.find("input.search-flag:checked");
      checked.each(function() {
        var elem = $(this);
        var param = elem.attr("name");
        var param_field = params[param] || [];
        param_field.push(elem.val());
        params[param] = param_field;
      });

      // Dynamically collect all inputs marked using".search-param". These
      // fields are exclusively non-nested, hence no need to collect them into
      // an array (unlike checkboxes)
      var search_params = this.$el.find(".search-param");
      search_params.each(function() {
        var elem = $(this);
        var param = elem.attr("name");
        var value = elem.val();
        if (!value) {
          return;
        }
        params[param] = value;
      });

      // handle search string
      params["search"] = this.$el.find("#prefix-tree-query").val();
      return params;
    },

    // Update search parameters and execute a search
    updateSearch: function() {
      this.model.set("queryParams", this._getSearch());
      this.doSearch();
    },

    doSearch: function() {
      globalCh.vent.trigger("search:update", this.model.get('queryParams'));
    },

    initialize: function() {
      this.fsm.setState("SIMPLE_SEARCH");
    }

  });

});

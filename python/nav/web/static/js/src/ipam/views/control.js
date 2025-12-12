define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");

  var viewStates = {
    "SEARCH": {
      "RESET": "SEARCH"
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
          "SEARCH": "advancedSearch"
        }
      }
    },

    regions: {
      "advanced": ".prefix-control-form-advanced"
    },

    events: {
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
      net_type: ["scope"],
      organization: null,
      usage: null,
      vlan: null,
      description: null
    },

    advancedSearch: function(self) {
      // Reset model TODO load from localstorage?
      self.debug("Reset query params");
      self.model.set("queryParams", self.advancedSearchDefaults);
      self.doSearch();
    },

    onRender: function() {
      // Detect select2 inputs
      this.$el.find(".select2").select2();
      // Set up remote fetching of prefixes for form auto-completion
      var prefixSelect = this.$el.find("#prefix-search-box");
      prefixSelect.select2({
        placeholder: 'Search for prefix...',
        minimumInputLength: 1,
        allowClear: true,
        ajax: {
          url: "/api/prefix/search/",
          dataType: 'json',
          type: "GET",
          delay: 250,
          data: function (params) {
            return {
              net_address: params.term, // search term
              page: params.page || 1
            };
          },
          processResults: function (data, params) {
            return {
              results: $.map(data, function (item) {
                return {
                  text: item.net_address,
                  id: item.net_address
                };
              })
            };
          },
          cache: true
        }
      });
      prefixSelect.on('change', this.forceSearch.bind(this));
      // Make sure net_type select always reflects default value. This is mostly
      // needed for the initial rendering.
      this.$el.find("#prefix-net-type").val(this.model.get("queryParams").net_type).trigger('change');
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
      this.fsm.setState("SEARCH");
    }

  });

});

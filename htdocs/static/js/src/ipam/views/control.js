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
      "input .prefix-tree-query": "updateSearch",
      "change .search-param": "updateSearch",
      "change .search-flag": "updateSearch",
      "change .net_types": "updateNetTypes",
      "click .toggleAdvanced": "toggleAdvanced",
      "keypress .search-param": "forceSearch"
    },

    updateNetTypes: function(evt) {
      var elem = $(evt.target);
      console.log(elem.val());
    },

    // Activate advanced form
    toggleAdvanced: function() {
      this.fsm.step(this.fsm.events.TOGGLE_ADVANCED);
      this.debug("Toggling advanced search");
      this.render();
      // make datetimepicker detect forms
      $(".datetimepicker").datetimepicker({
        'dateFormat': 'yy-mm-dd',
        'timeFormat': 'HH:mm'
      });
    },

    simpleSearch: function(self) {
      // Reset model
      self.debug("Reset query params");
      self.model.set("queryParams", {
        net_type: ["scope"],
        ip: null,
        search: null
      });
      self._updateSearch();
    },

    advancedSearch: function(self) {
      // Reset model TODO load from localstorage?
      self.debug("Reset query params");
      self.model.set("queryParams", {
        type: ["ipv4", "ipv6", "rfc1918"],
        net_type: ["scope"],
        timestart: null,
        timeend: null,
        organization: null,
        usage: null,
        vlan: null,
        description: null
      });
      self._updateSearch();
    },

    // Force defaults when control element is mounted on the DOM
    onAttach: function() {
      this._updateSearch();
    },

    onRender: function() {
      var advancedSearch = this.model.get("advancedSearch");
      var self = this;
      // Detect select2 inputs
      this.$el.find(".select2").select2();
    },

    forceSearch: function(evt) {
      if (evt.which === 13 || !evt.which) {
        evt.preventDefault();
        this._updateSearch();
      }
    },

    _updateSearch: function() {
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
      // update globally
      this.model.set("queryParams", params);
      globalCh.vent.trigger("search:update", params);
    },

    initialize: function() {
      this.updateSearch = _.throttle(this._updateSearch, 1000);
      this.fsm.setState("SIMPLE_SEARCH");
    }

  });

  var ControlAdvancedView = Marionette.ItemView.extend({
    template: "#prefix-control-form-advanced"
  });

});

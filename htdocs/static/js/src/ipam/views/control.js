define(function(require, exports, module) {
  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");

  var Models = require("src/ipam/models");
  var Viz = require("src/ipam/viz");

  var debug = require("src/ipam/util").ipam_debug;
  var globalCh = Backbone.Wreqr.radio.channel("global");

  // Control form for tree
  module.exports = Marionette.LayoutView.extend({
    debug: debug.new("views:control"),
    template: "#prefix-control-form",

    regions: {
      "advanced": ".prefix-control-form-advanced"
    },

    events: {
      "input .prefix-tree-query": "updateSearch",
      "change .search-param": "updateSearch",
      "change .search-flag": "updateSearch",
      "change .net_types": "updateNetTypes",
      "click .toggleAdvanced": "toggleAdvanced"
    },

    updateNetTypes: function(evt) {
      var elem = $(evt.target);
      console.log(elem.val());
    },

    // Activate advanced form
    toggleAdvanced: function() {
      var advancedSearch = this.model.get("advancedSearch");
      this.debug("Displaying advanced search => " + !advancedSearch);
      this.model.set("advancedSearch", !advancedSearch);
      this.render();
      // make datetimepicker detect forms
      $(".datetimepicker").datetimepicker({
        'dateFormat': 'yy-mm-dd',
        'timeFormat': 'HH:mm'
      });
    },

    onRender: function() {
      var advancedSearch = this.model.get("advancedSearch");
      var self = this;
      if (advancedSearch) {
        this.showChildView("advanced", new ControlAdvancedView({
          model: self.model
        }));
      }
      // Detect select2 inputs
      this.$el.find(".select2").select2();
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
    }

  });

  var ControlAdvancedView = Marionette.ItemView.extend({
    template: "#prefix-control-form-advanced"
  });

});

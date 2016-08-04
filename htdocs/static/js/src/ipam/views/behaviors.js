define(function(require, exports, module) {

  var _ = require("libs/underscore");
  var Backbone = require("backbone");
  var Marionette = require("marionette");
  var FSM = require("libs/statist");

  var Behaviors = {};

  // Simple mixin to add a state machine to a view. See 'subnetallocator.js' for
  // example usage.
  Behaviors.StateMachine = Marionette.Behavior.extend({
    defaults: {
      // States of the FSM
      "states": {},
      // TODO: model field?
      // Configure/handle the FSM after instantion
      "init": function(fsm) {
        return fsm;
      },
      // Field to update in model when state changed
      "modelField": null,
      // Handlers for each state
      handlers: {}
    },

    initialize: function() {
      var states = this.options.states;
      var modelField = this.options.modelField;
      var fsm = this.options.init(new FSM(states));
      if (!_.isObject(fsm)) {
        throw new Error("FSM init error: Didn't (or forgot to) return FSM object in 'init' function");
      }
      var self = this.view;
      // Update model with current state if modelField given
      if (modelField) {
        fsm.onChange(function (nextState) {
          self.model.set(modelField, nextState);
        });
      }
      // Mount handlers (if any). This is used to make a single function
      // responsible for any state in the state machine.
      _.each(this.options.handlers, function(handler, state) {
        var fn = self[handler];
        if (!_.isFunction(fn)) {
          throw new Error("Handler " + handler + " is not a function (or undefined)");
        }
        fsm.on(state, self[handler].bind(this, self));
      });
      self.fsm = fsm;
    }
  });


  // Marionette needs to be told where to find the behaviors. This utility
  // function takes care of this.
  function mount() {
    window.Behaviors = Behaviors;
    Marionette.Behaviors.behaviorsLookup = function() {
      return window.Behaviors;
    };
  };

  module.exports = mount;

});

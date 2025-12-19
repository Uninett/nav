define(function(require, exports, module) {

  const _ = require("libs/underscore");
  const Backbone = require("backbone");
  const Marionette = require("marionette");
  const FSM = require("libs/statist");

  // Simple mixin to add a state machine to a view. See 'subnetallocator.js' for
  // example usage.
  //
  // In Marionette v4, behaviors are referenced directly by class using
  // `behaviorClass` in the view's behaviors hash.
  const StateMachine = Marionette.Behavior.extend({
    initialize: function() {
      // In Marionette v4, use getOption() to access options with defaults
      const states = this.getOption('states') || {};
      const modelField = this.getOption('modelField');
      const initFn = this.getOption('init') || function(fsm) { return fsm; };
      const handlers = this.getOption('handlers') || {};

      const fsm = initFn(new FSM(states));
      if (!_.isObject(fsm)) {
        throw new Error("FSM init error: Didn't (or forgot to) return FSM object in 'init' function");
      }
      const self = this.view;
      // Update model with current state if modelField given
      if (modelField) {
        fsm.onChange(function (nextState) {
          self.model.set(modelField, nextState);
        });
      }
      // Mount handlers (if any). This is used to make a single function
      // responsible for any state in the state machine.
      _.each(handlers, function(handler, state) {
        const fn = self[handler];
        if (!_.isFunction(fn)) {
          throw new Error("Handler " + handler + " is not a function (or undefined)");
        }
        fsm.on(state, self[handler].bind(this, self));
      });
      self.fsm = fsm;
    }
  });

  // Export behaviors directly for use with behaviorClass in Marionette v4
  module.exports = {
    StateMachine: StateMachine
  };

});

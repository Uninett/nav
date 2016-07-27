// Simple FSM shim. It simply maps states to state maps, which in turn map
// events to the next state. The next state might also be a function, which is
// called (and passed any event data) and returns the next state. The state map
// is validated upon initialization, to ensure that we never enter an undefined
// or invalid state. It also supports listening to when a a state is entered
// ('.on', '.once'), usually for asynchronous operations like global resets.
// These listeners are passed any event data leading into the desired state.
//
// The purpose of this shim is to make sure somewhat more complex components
// (typically views) always have a well-defined, verified state, which
// simplifies business logic. It can also be used to ensure certain events have
// been fired, without using model variables like 'hasGreetedUserOnce'.
//
// Example usage:
//
//     var fsm = new FSM({
//       init: { activate: "active" }
//       active: { reset: "init" }
//     })
//     fsm.state // => "init"
//     fsm.step("activate") // => "active"
//     fsm.step(fsm.events.INIT.ACTIVATE) // equivalent
//     fsm.state // => "active"
//     fsm.step(null) // not matched, retains "active" state
//     fsm.on("active", function() { console.log("woho"); }) // called every time active is entered
//     fsm.once("active", function() { console.log("woho"); }) // called only once
//     fsm.setstate("undefined") // throws an error
//     fsm.setState(fsm.states.INIT)

define(function (require, exports, module) {
  var _ = require("libs/underscore");

  var FSM = function(stateMap) {
    var defaultMap = { INIT: {} };
    // Maps states to event handlers (state maps), which map events to new states
    this.fsm = Object.assign(defaultMap, stateMap);
    // By convention, "INIT" is the default state and always defined
    this.state = "INIT";
    // List of all possible actions (enum-like) for each state
    this.events = _.reduce(this.fsm, function(memo, stateMap, state) {
      var actions = _.keys(stateMap);
      memo[state] = _.reduce(actions, function(enums, action) {
        enums[action] = action;
        return enums;
      }, {});
      return memo;
    }, {});
    // Friendly list of all possible states (enum-like), probably useful
    var states = _.keys(this.fsm);
    this.states = _.reduce(states, function(memo, state) {
      memo[state] = state;
      return memo;
    }, {});
    // Initialize listeners
    this.listeners = _.reduce(states, function(memo, state) {
      memo[state] = [];
      return memo;
    }, {});
    // Freeze fsm to avoid mutation
    Object.freeze(this.fsm);
    Object.freeze(this.states);
    Object.freeze(this.events);
    // Return validation value
    return this.validate();
  };

  // Validate the whole stateMap to ensure we are able to reach all possible
  // states.
  var noStateTemplate = _.template("FSM error: Trying to move from '<%= currentState %>' to '<%= state %>' (via <%= via %>), which is not defined");
  FSM.prototype.validate = function() {
    var self = this;
    _.each(self.fsm, function(stateMap, state) {
      _.each(stateMap, function(nextState, action) {
        // Cannot validate functions just now
        if (_.isFunction(nextState)) {
          return;
        }
        if (!_.has(self.fsm, nextState)) {
          var s = noStateTemplate({
            state: nextState,
            currentState: state,
            via: "event '" + action + "'"
          });
          throw new Error(s);
        }
      });
    });
  };

  // Notify all listeners of the current state
  FSM.prototype.notifyAll = function(eventData) {
    var self = this;
    var state = this.state;
    // Return true if we want to remove the listener
    this.listeners[state] = _.reject(self.listeners[state], function(callbackMap) {
      callbackMap.fn(eventData);
      return callbackMap.type === "once";
    });
  };

  // Update current state to nextState and notify listeners
  FSM.prototype.setState = function(nextState, eventData) {
    var self = this;
    if (_.isFunction(nextState)) {
      nextState = nextState(eventData);
    }
    if (!_.has(self.fsm, nextState)) {
      var s = noStateTemplate({ state: nextState, currentState: self.state, via: "setState()" });
      throw new Error(s);
    }
    this.state = nextState;
    this.notifyAll(eventData);
    return nextState;
  };

  // Make the FSM react to some event
  FSM.prototype.step = function(event, eventData) {
    var currentStateMap = this.fsm[this.state];
    // Ignore events for which no next state is defined
    if (!_.has(currentStateMap, event)) {
      console.log("Warning: Couldn't catch event", event, "looping...");
      return this.currentState;
    }
    var nextState = currentStateMap[event];
    return this.setState(nextState, eventData);
  };

  // Utility function to register functions
  FSM.prototype.__addListener = function(desiredState, callbackMap) {
    var self = this;
    if (!_.has(self.listeners, desiredState)) {
      console.log("Warning: Trying to listen to state", desiredState, ", which is undefined. Ignoring.");
      return;
    }
    this.listeners[desiredState].push(callbackMap);
  };

  // Calls callback every time desiredState is entered
  FSM.prototype.on = function(desiredState, callback) {
    this.__addListener(desiredState, {
      fn: callback,
      type: "on"
    });
  };

  // Calls callback *once* if desiredState is entered
  FSM.prototype.once = function(desiredState, callback) {
    this.__addListener(desiredState, {
      fn: callback,
      type: "once"
    });
  };

  module.exports = FSM;

});

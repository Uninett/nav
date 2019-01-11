//
// Copyright (C) 2016 Uninett AS
//
// This file is part of Network Administration Visualized (NAV).
//
// NAV is free software: you can redistribute it and/or modify it under
// the terms of the GNU General Public License version 3 as published by
// the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
// more details.  You should have received a copy of the GNU General Public
// License along with NAV. If not, see <http://www.gnu.org/licenses/>.
//
// == STATIST, A SIMPLE FSM LIBRARY
//
// Simple FSM shim. It simply maps states to state maps, which in turn map
// events to the next state. The next state might also be a function, which is
// called (and passed any event data) and returns the next state. The state map
// is validated upon initialization, to ensure that we never enter an undefined
// or invalid state. It also supports listening to when a a state is entered
// ('.on', '.once'), usually for asynchronous operations like global resets.
// These listeners are passed any event data leading into the desired state.
//
// Do note that events that map to null are considered no-ops, and will not be
// handled in any way. This is to allow for clean override.
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
//     fsm.step(fsm.events.activate) // equivalent
//     fsm.state // => "active"
//     fsm.step(null) // not matched, retains "active" state
//     fsm.on("active", function() { console.log("woho"); }) // called every time active is entered
//     fsm.once("active", function() { console.log("woho"); }) // called only once
//     fsm.setstate("undefined") // throws an error
//     fsm.setState(fsm.states.init)
//
// For mixins and inheritance, we offer two similar function:
// extends(originalState, mixinOrAnotherState) and mixin(originalState,
// mixinOrAnotherState). In the former case, any value in originalState will
// override the one defined in the argument, e.g. it works like typical OOP
// inheritance. With mixin(), the mixin or state we're extending from will
// always override any values defined in originalState. Do note that these
// operations also are validated and subject to the same requirements as
// defining the map up front, but allows for explicit reuse of components via
// mixins or simple parent-child inheritance.

define(function (require, exports, module) {
  var _ = require("libs/underscore");

  var FSM = function(stateMap) {
    var defaultMap = { INIT: {} };
    // Maps states to event handlers (state maps), which map events to new states
    this.fsm = defaultMap;
    _.extend(this.fsm, stateMap);
    // By convention, "INIT" is the default state and always defined
    this.state = "INIT";
    // Trigger for when a new state is entered
    this.__onChange = [];
    // List of all possible actions (enum-like) for each state
    this.events = this.getEvents();
    // Friendly list of all possible states (enum-like), probably useful
    this.states = this.getStates();
    // Initialize listeners
    this.listeners = _.reduce(this.states, function(memo, state) {
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

  // Returns the events the FSM can respond to (enum-like)
  FSM.prototype.getEvents = function() {
    return _.reduce(this.fsm, function(memo, stateMap) {
      _.each(stateMap, function(state, event) {
        memo[event] = event;
      });
      return memo;
    }, {});
  };

  // Returns a list of states the FSM can be in (enum-like)
  FSM.prototype.getStates = function() {
    var states = _.keys(this.fsm);
    return _.reduce(states, function(memo, state) {
      memo[state] = state;
      return memo;
    }, {});
  };

  // Validate the whole stateMap to ensure we are able to reach all possible
  // states, and that we only reach defined states.
  var noStateTemplate = _.template("FSM error: Trying to move from '<%= currentState %>' to '<%= state %>' (via <%= via %>), which is not defined");
  var notReachableTemplate = _.template("FSM warning: State '<%= state %>' cannot be reached from any other state");
  FSM.prototype.validate = function() {
    var self = this;
    // Map of each state we can reach
    var reachable = _.reduce(_.keys(self.fsm), function(memo, state) {
      memo[state] = state === "INIT" ? true : false;
      return memo;
    }, {});
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
        reachable[nextState] = true;
      });
    });
    _.each(reachable, function(isReachable, state) {
      if (!isReachable) {
        var s = notReachableTemplate({ state: state });
        console.log(s);
      }
    });
    return true;
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
    // Call onChange callbacks
    _.each(self.__onChange, function (callback) {
      callback(nextState);
    });
    this.notifyAll(eventData);
    return nextState;
  };

  // Make the FSM react to some event
  FSM.prototype.step = function(event, eventData) {
    var currentStateMap = this.fsm[this.state];
    // Ignore events for which no next state is defined
    if (!_.has(currentStateMap, event)) {
      var stack = new Error().stack;
      console.log("Warning: Couldn't catch event", event, ", therefore ignoring. Current state:", this.state, " Stack:", stack);
      return this.currentState;
    }
    var nextState = currentStateMap[event];
    // Events that return null should not be handled
    if (nextState === null) {
      return this.currentState;
    }
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

  // Called whenever the state changes
  FSM.prototype.onChange = function(callback) {
    this.__onChange.push(callback);
  };

  // Make targetState inherit values from an existing state or state map. Does
  // not override any values already defined in targetStat
  FSM.prototype.extends = function(targetState, stateOrStateMap) {
    this.__inherit(targetState, stateOrStateMap, false);
  };

  // Make targetState inherit values from an existing state or state map. Does
  // override any values already defined in targetStat
  FSM.prototype.mixin = function(targetState, stateOrStateMap) {
    this.__inherit(targetState, stateOrStateMap, true);
  };

  // Utility function to update an existing state and either make it inherit
  // from a statemap or be extended by it. See .mixin() and .extends()
  var missingTemplate = _.template("Trying to extend existing state '<%= state %>', but it doesn't exist.");
  FSM.prototype.__inherit = function(toExtend, stateOrStateMap, destructiveExtend) {
    // Check that the state we have defined is defined
    if (!_.has(this.fsm, toExtend)) {
      throw new Error(missingTemplate({ state: toExtend }));
    };
    // We're trying to inherit from another state
    if (_.isString(stateOrStateMap)) {
      if (!_.has(this.fsm, stateOrStateMap)) {
        throw new Error(missingTemplate({ state: stateOrStateMap }));
      }
      stateOrStateMap = this.fsm[stateOrStateMap];
    }
    // Temporarily unfreeze FSM
    var tmp = {};
    _.extend(tmp, this.fsm);
    this.fsm = tmp;
    var originalState = this.fsm[toExtend];
    var newState = {};
    if (destructiveExtend) {
      _.extend(newState, originalState, stateOrStateMap);
    } else {
      _.extend(newState, stateOrStateMap, originalState);
    }
    this.fsm[toExtend] = newState;
    // Update public API to reflect any changes, if any
    this.states = this.getStates();
    this.events = this.getEvents();
    // Refreeze
    Object.freeze(this.fsm);
    Object.freeze(this.states);
    Object.freeze(this.events);
    // Make sure we validate afterwards
    this.validate();
  };

  module.exports = FSM;

});

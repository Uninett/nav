/*
 * The Backbone.EventBroker adds a general purpose Event Broker implementation
 * to Backbone based on the Backbone Events API. The EventBroker can be used
 * directly to serve as a centralized event management mechanism for an entire
 * application. Additional, context specific, namespaced brokers can also be
 * created in order to provide unique brokers within a particular part of an
 * application.
 */
Backbone.EventBroker = Backbone.EventBroker || ( function() {
    // Defines the cache which contains each namespaced EventBroker instance
    var _brokers = {};

    /*
     * Implements the registering and unregistering of event/callback mappings
     * for specific objects registered with an EventBroker.
     */
    var _registration = function( interests, context, broker, method ) {
        if ( !context && interests.interests ) {
            context   = interests;
            interests = interests.interests;
        }
        for ( var event in interests ) {
            if (interests.hasOwnProperty(event)) {
                broker[ method ]( event, context[ interests[event] ], context );
            }
        }
        return broker;
    };

    /*
     * Defines an Event registry which allows for registering and unregistering
     * multiple events/callbacks. This API is similar to Backbone.Events.on in
     * that it maps events to callbacks as well as a context. The main difference
     * is that mutliple event / callback mappings can be created as one-to-one
     * mappings for a given context.
     */
    var EventRegistry = {
        /*
         * Provides a convenience method which is similar to Backbone.Events.on
         * in that this method binds events to callbacks. The main difference is
         * that this method allows for binding multiple events / callbacks which
         * have a single context.
         *
         * This method can be invoked with two arguments, the first being an object
         * of event types as keys, whose values are the callbacks to which the events
         * are bound (as described above), and the second argument is the context
         * object typically (this) which specifies the context against which the
         * events and callbacks are to be invoked.
         *
         * This method can also be invoked with a single object which defines an
         * 'interests' property which defines a hash containing event types as
         * keys, and callbacks as values.
         *
         * <pre>
         *
         * // Register event/callbacks based on a hash and associated context
         * var Users = Backbone.Collection.extend(
         * {
         *     broker: Backbone.EventBroker,
         *
         *     initialize: function()
         *     {
         *         this.broker.register({
         *             'user:select'   : 'select',
         *             'user:deselect' : 'deselect',
         *             'user:edit'     : 'edit',
         *             'user:update'   : 'update',
         *             'user:remove'   : 'remove'
         *         }, this );
         *     },
         *     select: function() { ... },
         *     deselect: function() { ... },
         *     edit: function() { ... },
         *     update: function() { ... },
         *     remove: function() { ... }
         * });
         * </pre>
         *
         * <pre>
         *
         * // Register event/callbacks based on an object's "interest" property.
         * var User = Backbone.Model.extend(
         * {
         *     broker: Backbone.EventBroker,
         *
         *     interests : {
         *         'user:select'   : 'select',
         *         'user:deselect' : 'deselect',
         *         'user:edit'     : 'edit',
         *         'user:update'   : 'update',
         *         'user:remove'   : 'remove'
         *     },
         *     initialize: function() {
         *         this.broker.register( this );
         *     },
         *     select: function() { ... },
         *     deselect: function() { ... },
         *     edit: function() { ... },
         *     update: function() { ... },
         *     remove: function() { ... }
         * });
         * </pre>
         *
         */
        register: function( interests, context ) {
            if ( interests || context ) {
                return _registration( interests, context, this, 'on' );
            }
            return this;
        },

        /*
         * Provides a convenience method which is similar to Backbone.Events.off
         * in that this method unbinds events from callbacks. The main difference
         * is this method allows for unbinding multiple events / callbacks.
         *
         * This method can also be invoked with a single object which provides an
         * 'interests' property which defines a hash containing event types as keys,
         * and the callbacks to which the events were previosuly bound as values.
         *
         * This method can also be invoked with two arguments, the first being an
         * object of event types as keys, whose values are the callbacks to which
         * the events are bound (as described above), and the second argument is
         * context object typically (this) which specifies the context to which the
         * events and callbacks were bound.
         *
         * <pre>
         *
         * var UserView = Backbone.View.extend(
         * {
         *     interests: {
         *         'user:select'   : 'select',
         *         'user:deselect' : 'deselect'
         *     },
         *     initialize: function() {
         *         Backbone.EventBroker.register( this );
         *     },
         *     remove: function() {
         *         Backbone.EventBroker.unregister( this );
         *     },
         *     select: function() { ... },
         *     deselect: function() { ... }
         * });
         * </pre>
         *
         */
        unregister: function( interests, context ) {
            if ( interests || context ) {
                return _registration( interests, context, this, 'off' );
            }
            return this;
        }
    };

    // creates and returns the EventBroker ...
    return _.extend({
        /*
         * Defines the default EventBroker namespace - an empty string. Specific
         * EventBrokers created via EventBroker.get( namespace ) will be created
         * and have their namespace property assigned the value of the namespace
         * specified.
         *
         */
        namespace: '',

        /*
         * Retrieves the broker for the given namespace. If a broker has yet to
         * have been created, it will be created for the namespace and returned.
         * Subsequent retievals for the broker of the same namespace will return
         * a reference to the same broker; that is, only one unique broker will
         * be created per namespace.
         *
         */
        get: function( namespace ) {
            if ( _brokers[ namespace ] === undefined ) {
                _brokers[ namespace ] = _.extend( { 'namespace': namespace }, Backbone.Events, EventRegistry );
            }
            return _brokers[ namespace ];
        },

        /*
         * Determines if the specified broker has been created for the given
         * namespace.
         *
         */
        has: function( namespace ) {
            return _brokers[ namespace ] !== undefined;
        },

        /*
         * Destroys the broker for the given namespace, or multiple brokers for
         * a space delimited string of namespaces. To destroy all brokers that
         * have been created under any namespace, simply invoke this method with
         * no arguments.
         *
         */
        destroy: function( namespace ) {
            if ( !namespace ) {
                for ( namespace in _brokers ) {
                    if (_brokers.hasOwnProperty(namespace)) {
                        this.destroy( namespace );
                    }
                }
            }
            else if ( _brokers[ namespace ] ) {
                _brokers[ namespace ].off();
                delete _brokers[ namespace ];
            }
            return this;
        }
    }, Backbone.Events, EventRegistry );

}());
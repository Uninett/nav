define([
    'libs-amd/text!resources/networkexplorer/router.html',
    'libs-amd/text!resources/networkexplorer/gwport.html',
    'libs-amd/text!resources/networkexplorer/swport.html',
    'libs-amd/text!resources/networkexplorer/switch.html',
    'libs/jquery',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/handlebars'], function (routerTemplate,
                                  gwportTemplate,
                                  swportTemplate,
                                  switchTemplate) {


    Handlebars.registerHelper('equal', function(lvalue, rvalue, options) {
        if (arguments.length < 3) {
            throw new Error("Handlebars Helper equal needs 2 parameters");
        } else if(lvalue !== rvalue) {
            return options.inverse(this);
        } else {
            return options.fn(this);
        }
    });


    var Node = Backbone.Model.extend({
        // Node base class

        idAttribute: 'pk',

        defaults: {
            pk: -1,
            type: 'root',
            state: 'collapsed',
            expandable: true
        },

        initialize: function () {
            this.setUrl();
        },

        setUrl: function () {
            switch (this.get('type')) {
                 case 'root':
                    this.url = 'routers/';
                    break;
                case 'router':
                    var routerId = this.get('pk');
                    this.url = 'expand/router/' + routerId + '/';
                    break;
                case 'gwport':
                    var gwPortId = this.get('pk');
                    this.url = 'expand/gwport/' + gwPortId + '/';
                    break;
                case 'swport':
                    var url;
                    var switchId = this.get('switch_id');
                    if (switchId) {
                        url = 'expand/switch/' + switchId + '/';
                        var vlanId = this.get('vlan_id');
                        if (vlanId) {
                            url += 'vlan/' + vlanId + '/';
                        }
                    } else {
                        var swPortId = this.get('pk');
                        url = 'expand/swport/' + swPortId + '/';
                    }
                    this.url = url;
                    break;
            }
        },

        elementId: function () {
            if (this.get('type') !== 'root') {
                return this.get('type') + '-' + this.get('pk');
            }  else {
                return 'root';
            }
        },

        expand: function () {

            /*
            Expands the node if its expandable and not currently
            processing. Fetches the nodes children from the
            server if necessary. Triggers a rerender of the
            entire tree FIXME (only render subnodes).
             */

            console.log('in expand');

            if (!this.get('expandable') || this.get('state') === 'processing') {
                console.log('can not expand');
                return;
            }

            this.set('state', 'processing');

            var children = this.getChildren();

            if (children.length === 0) {

                var node = this;
                children.fetch({
                    success: function () {
                        node.set('state', 'expanded');
                        node.set('children', children);
                        Backbone.EventBroker.trigger('tree:render', node);
                    },
                    error: function () {
                        console.log('could not fetch nodes');
                        node.set('state', 'collapsed');
                    }
                });
            } else {
                console.log('Yay! children already fetched');
                this.set('state', 'expanded');
                Backbone.EventBroker.trigger('tree:render', this);
            }
        },

        collapse: function () {

            console.log('collapsing node');

            if (this.get('state') === 'collapsed') {
                return;
            }

            this.set('state', 'collapsed');
            Backbone.EventBroker.trigger('tree:render', this);
        },

        getChildren: function () {
            var c;
            if (!this.get('children')) {
                c = new NodeCollection();
            } else {
                c = this.get('children');
            }
            c.url = this.url;
            return c;
        }
    });

    var NodeCollection = Backbone.Collection.extend({

        /*
        A collection for Node-models. Used to hold
        a Nodes children.
         */

        model: Node
    });

    var Tree = Backbone.Model.extend({
        // The network tree

        defaults: {
            root: new Node()
        },

        expand: function () {

            this.get('root').expand();
        },

        collapse: function () {

            this.get('root').collapse();
        }
    });

    /**
     * Views
     */
    var TreeView = Backbone.View.extend({

        el: '#networktree',

        interests: {
            'tree:render': 'render'
        },

        initialize: function () {

            // Registering for events
            Backbone.EventBroker.register(this);
        },

        render: function (node) {

            /*
            Renders the tree recursively starting with the
            root node
             */

            if (node.get('type') === 'root') {

                console.log('rendering from root');
                var rootView = new NodeView({model: node});
                var nodes = $('<ul>');
                nodes.html(rootView.render().el);
                this.$el.html(nodes);

            } else {

                console.log('rendering from ' + node.elementId());
                var nodeView = new NodeView({model: node});
                var element = this.$el.find('#' + node.elementId());
                nodeView.setElement(element);
                nodeView.render();
            }

            return this;
        }
    });

    var NodeView = Backbone.View.extend({

        tagName: 'li',
        className: 'node',

        initialize: function () {
            var template;
            switch (this.model.get('type')) {
                case 'router':
                    template = routerTemplate;
                    break;
                case 'gwport':
                    template = gwportTemplate;
                    break;
                case 'swport':
                    template = swportTemplate;
                    break;
                case 'switch':
                    template = switchTemplate;
            }

            this.template = Handlebars.compile(template);

            this.$el.attr('id', this.model.elementId());
        },

        render: function () {

            /*
            Renders the node, and also its children if the
            node is expanded.
             */

            if (this.model.get('type') !== 'root') {

                this.$el.html(this.template(this.model.toJSON()));
                this.registerExpandTrigger();
            } else {
               this.$el.html($('<ul class="children">'));
            }

            if (this.model.get('state') === 'expanded') {

                var children = this.model.get('children');
                var children_elem = this.$('.children');
                var last_index = children.length - 1;

                children.each(function (child, i) {

                    var childView = new NodeView({model: child});
                    if (i === last_index) {
                        child.set('end', true);
                    }

                    children_elem.append(childView.render().el);
                });
            }
            return this;
        },

        showSpinner: function () {
          this.$('img').attr('src', '/images/main/process-working.gif');
        },

        registerExpandTrigger: function () {

            /*
            Bind 'triggerExpand' event to the collapse/expand image
            if the node is expandable.
             */

            if (this.model.get('expandable')) {
                var expandButton = this.$('img');
                expandButton.on('click', _.bind(this.triggerExpand, this));
            }
        },

        triggerExpand: function () {

            /*
            Expands or collapses a node based on its state.
            Is bound to click event on the expand-/collapse-icon
             */

            console.log('caught expand on ' + this.model.elementId());

            if (this.model.get('state') === 'collapsed') {
                this.showSpinner();
                this.model.expand();
            } else if (this.model.get('state') === 'expanded') {
                this.model.collapse();
            }
        }
    });

    var NetworkView = new TreeView({model: new Tree()});
    var RootNodeView = new NodeView({model: NetworkView.model.get('root')});

    NetworkView.model.expand();
});
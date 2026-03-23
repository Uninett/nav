define([
    'libs-amd/text!resources/networkexplorer/router.html',
    'libs-amd/text!resources/networkexplorer/gwport.html',
    'libs-amd/text!resources/networkexplorer/swport.html',
    'libs-amd/text!resources/networkexplorer/switch.html',
    'libs-amd/text!resources/networkexplorer/swport_leaf.html',
    'libs/handlebars',
    'libs/backbone',
    'libs/backbone-eventbroker'
                     ], function (routerTemplate,
                                  gwportTemplate,
                                  swportTemplate,
                                  switchTemplate,
                                  leafTemplate,
                                  Handlebars
                                 ) {


    Handlebars.registerHelper('equal', function(lvalue, rvalue, options) {
        if (arguments.length < 3) {
            throw new Error("Handlebars Helper equal needs 2 parameters");
        } else if(lvalue !== rvalue) {
            return options.inverse(this);
        } else {
            return options.fn(this);
        }
    });


    const Node = Backbone.Model.extend({

        /*
         * An object representing a node in the network tree.
         * Can be any kind of device/interface.
         */

        idAttribute: 'pk',

        defaults: {
            pk: -1,
            type: 'root',
            state: 'collapsed',
            expandable: false,
            matched: false,
            navImagePath: NAV.imagePath
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
                    this.url = `expand/router/${this.get('pk')}/`;
                    break;
                case 'gwport':
                    this.url = `expand/gwport/${this.get('pk')}/`;
                    break;
                case 'swport': {
                    const switchId = this.get('switch_id');
                    if (switchId) {
                        const vlanId = this.get('vlan_id');
                        this.url = vlanId
                            ? `expand/switch/${switchId}/vlan/${vlanId}/`
                            : `expand/switch/${switchId}/`;
                    } else {
                        this.url = `expand/swport/${this.get('pk')}/`;
                    }
                }
                    break;
            }
        },

        elementId: function () {
            if (this.get('type') !== 'root') {
                return `${this.get('type')}-${this.get('pk')}`;
            } else {
                return 'root';
            }
        },

        expand: function (d) {

            /*
             * Expands the node if its expandable and not currently
             * processing. Fetches the nodes children from the
             * server if necessary. Triggers a rerender of the
             * node and it's subtree.
             */

            console.log('in expand');

            if (!this.get('expandable') || this.get('state') === 'processing') {
                console.log('can not expand');
                return;
            }

            this.set('state', 'processing');

            const children = this.getChildren();

            if (children.length === 0) {
                children.fetch({
                    success: () => {
                        this.set('state', 'expanded');
                        Backbone.EventBroker.trigger('tree:render', this);
                        if (d?.resolve) d.resolve();
                    },
                    error: (collection, response) => {
                        if (response.status === 401) {
                            // If no longer authorized, reload the page
                            location.reload();
                        }
                        console.log('Error fetching children nodes');
                        this.set('state', 'collapsed');
                        if (d?.reject) d.reject();
                    }
                });
            } else {
                console.log('Yay! children already fetched');
                this.set('state', 'expanded');
                Backbone.EventBroker.trigger('tree:render', this);
                if (d?.resolve) d.resolve();
            }
        },

        collapse: function () {

            /*
             * Collapses the nodes subtree and triggers a
             * rerender. The nodes children are kept.
             */

            console.log('collapsing node');

            if (this.get('state') === 'collapsed') {
                return;
            }

            this.set('state', 'collapsed');
            Backbone.EventBroker.trigger('tree:render', this);
        },

        getChildren: function () {
            if (!this.get('children')) {
                this.set('children', new NodeCollection());
            }
            const collection = this.get('children');
            collection.url = this.url;
            return collection;
        },

        match: function (d) {
            Backbone.EventBroker.trigger('node:match', this, d);
        }
    });

    const NodeCollection = Backbone.Collection.extend({

        /*
         * A collection for Node-models. Used to hold
         * a nodes children.
         */

        model: Node
    });

    const Tree = Backbone.Model.extend({

        /*
         * A Container-model for the tree.
         *
         * NOTE: Might not be necessary
         */

        defaults: {
            root: new Node({expandable: true})
        },

        expand: function () {

            this.get('root').expand({});
        },

        collapse: function () {

            this.get('root').collapse();
        }
    });


    const TreeView = Backbone.View.extend({

        /*
         * View-object for the Tree model.
         */

        el: '#networktree',

        interests: {
            'tree:search': 'search',
            'tree:render': 'render'
        },

        initialize: function () {

            // Registering for events
            Backbone.EventBroker.register(this);
        },

        search: function (data) {

            /*
             * Depth first search in the network tree that expands
             * and highlights matching nodes from the search response.
             */

            this.$el.find('.highlight').removeClass('highlight').addClass('node');

            const root = this.model.get('root');
            const routers = root.get('children');

            const hasResults = data.routers.length > 0 ||
                data.gwports.length > 0 ||
                data.swports.length > 0;

            routers.each((router) => {
                if (!hasResults && router.get('state') === 'expanded') {
                    router.collapse();
                    return;
                }

                if (data.routers.includes(router.get('pk'))) {
                    const dRouters = $.Deferred();
                    router.match(dRouters);
                    dRouters.done(() => this.expandMatchingGwports(router, data));
                }
            });
        },

        expandMatchingGwports: function (router, data) {
            const gwports = router.get('children');
            gwports.each((gwport) => {
                if (data.gwports.includes(gwport.get('pk'))) {
                    const dGWPorts = $.Deferred();
                    gwport.match(dGWPorts);
                    dGWPorts.done(() => this.highlightMatchingSwports(gwport, data));
                }
            });
        },

        highlightMatchingSwports: function (gwport, data) {
            const swports = gwport.get('children');
            swports.each((swport) => {
                if (data.swports.includes(swport.get('pk'))) {
                    swport.match();
                }
            });
        },

        render: function (node) {

            /*
             * Renders the tree recursively starting either
             * with the root or the node which triggered a
             * rerender-event.
             */

            if (node.get('type') === 'root') {
                console.log('rendering from root');
                const rootView = new NodeView({model: node});
                const nodes = $('<ul>');
                nodes.html(rootView.render().el);
                this.$el.html(nodes);
            } else {
                console.log(`rendering from ${node.elementId()}`);
                const nodeView = new NodeView({model: node});
                const element = this.$el.find(`#${node.elementId()}`);
                nodeView.setElement(element);
                nodeView.render();
            }

            return this;
        }
    });

    const NodeView = Backbone.View.extend({

        /*
         * View-object for the Node model
         */

        tagName: 'li',
        className: 'node',

        interests: {
            'node:match': 'match'
        },

        initialize: function () {
            let template;
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
                    break;
                case 'swport-leaf':
                    template = leafTemplate;
                    break;
            }

            if (template) {
                this.template = Handlebars.compile(template);
            }
            Backbone.EventBroker.register(this);

            this.listenTo(this.model.getChildren(), 'error', this.handleError);
            this.$el.attr('id', this.model.elementId());
        },

        handleError: function (collection, response) {
            this.hideSpinner();
            this.showError(`The request for more data failed (${response.status} - ${response.statusText}).`);
        },

        showError: function (text) {
            if (!this.errorElement) {
                this.errorElement = this.createErrorElement();
                this.errorElement.appendTo(this.$el);
            }
            this.errorElement.text(text).show();
            return this.errorElement;
        },

        createErrorElement: function () {
            return $('<span class="alert-box alert"></span>').on('click', function () {
                $(this).hide();
            });
        },

        render: function () {

            /*
             * Renders the node, and also its children if the
             * node is expanded.
             */

            if (this.model.get('type') !== 'root') {

                this.$el.html(this.template(this.model.toJSON()));
                this.registerExpandTrigger();
            } else {
                // The node is root and we don't need
                // to render it
               this.$el.html($('<ul class="children">'));
            }

            if (this.model.get('state') === 'expanded') {
                const children = this.model.get('children');
                const childrenElem = this.$('.children');
                const lastIndex = children.length - 1;

                children.each((child, i) => {
                    const childView = new NodeView({model: child});
                    if (i === lastIndex) {
                        child.set('end', true);
                    }

                    childrenElem.append(childView.render().el);
                });
            }
            return this;
        },

        showSpinner: function () {
            this.$('img').attr('src', `${NAV.imagePath}/main/process-working.gif`);
        },

        hideSpinner: function () {
            // This should only be called on a node that fails to expand
            // and therefore we know it's expandable.
            this.$('img').attr('src', `${NAV.imagePath}/networkexplorer/expand.gif`);
        },

        registerExpandTrigger: function () {

            // Bind 'triggerExpand' event to the collapse/expand image
            // if the node is expandable.
            if (this.model.get('expandable')) {
                const expandButton = this.$('img');
                expandButton.on('click', (e) => this.triggerExpand(e));
            }
        },

        triggerExpand: function (d) {

            /*
             * Expands or collapses a node based on its state.
             * Is bound to click event on the expand-/collapse-icon
             */

            console.log(`caught expand on ${this.model.elementId()}`);

            if (this.model.get('state') === 'collapsed' &&
                    this.model.get('expandable')) {
                this.showSpinner();
                this.model.expand(d);
            } else if (this.model.get('state') === 'expanded') {
                this.model.collapse();
            }
        },

        match: function (node, d) {
            if (node === this.model) {
                if (this.model.get('type') !== 'router') {
                    this.$el.attr('class', 'highlight');
                }
                this.model.set('matched', true);
                if (this.model.get('state') === 'expanded') {
                    this.model.collapse();
                }
                this.triggerExpand(d);
            }
        }
    });

    // Return a container exposing all objects
    return {
        Node: Node,
        Tree: Tree,
        NodeCollection: NodeCollection,
        NodeView: NodeView,
        TreeView: TreeView
    };
});

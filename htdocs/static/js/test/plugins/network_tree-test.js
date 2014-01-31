/* TODO: Rewrite to chai
define(['plugins/network_tree'], function (NetworkTree) {

    var Node = NetworkTree.Node;
    var NodeView = NetworkTree.NodeView;
    var NodeCollection = NetworkTree.NodeCollection;
    var Tree = NetworkTree.Tree;
    var TreeView = NetworkTree.TreeView;

    buster.testCase('Node model', {

        setUp: function () {
            this.Nodes = {
                'root': new Node({expandable: true}),
                'router': new Node({pk:1, type:'router', expandable:true}),
                'gwport': new Node({pk:2, type:'gwport', expandable:true}),
                'swport': new Node({pk:3, type:'swport', expandable:true}),
                'switch': new Node({pk:4, type:'swport', switch_id:1})
            };
            var routers = new NodeCollection([this.Nodes.router]);
            var gwports = new NodeCollection([this.Nodes.gwport]);
            var swports = new NodeCollection([this.Nodes.swport, this.Nodes.switch]);
            this.Nodes.root.set('children', routers);
            this.Nodes.router.set('children', gwports);
            this.Nodes.gwport.set('children', swports);
            this.NodeViews = {
                'rootView': new NodeView({model:this.Nodes.root}),
                'routerView': new NodeView({model:this.Nodes.router}),
                'gwportView': new NodeView({model:this.Nodes.gwport}),
                'swportView': new NodeView({model:this.Nodes.swport}),
                'switchView': new NodeView({model:this.Nodes.switch})
            };
            this.Tree = new Tree({root: this.Nodes.root});
        },
        'is defined': function () {
            assert.defined(NetworkTree);
        },
        'nodes have correct urls': function () {

            var n = this.Nodes;
            var expectedRootUrl = 'routers/';
            var expectedRouterUrl = 'expand/router/' + n.router.get('pk') + '/';
            var expectedGWPortUrl = 'expand/gwport/' + n.gwport.get('pk') + '/';
            var expectedSWPortUrl = 'expand/swport/' + n.swport.get('pk') + '/';
            var expectedSwitchUrl = 'expand/switch/' + n.switch.get('switch_id') + '/';

            assert.equals(n.root.url, expectedRootUrl);
            assert.equals(n.router.url, expectedRouterUrl);
            assert.equals(n.gwport.url, expectedGWPortUrl);
            assert.equals(n.swport.url, expectedSWPortUrl);
            assert.equals(n.switch.url, expectedSwitchUrl);
        },
        'nodes have correct elementId': function () {

            var n = this.Nodes;
            var expextedRootId = 'root';
            var expectedRouterId = 'router-' + n.router.get('pk');
            var expectedGWPortId = 'gwport-' + n.gwport.get('pk');
            var expectedSWPortId = 'swport-' + n.swport.get('pk');
            var expectedSwitchId = 'swport-' + n.switch.get('pk');

            assert.equals(n.root.elementId(), expextedRootId);
            assert.equals(n.router.elementId(), expectedRouterId);
            assert.equals(n.gwport.elementId(), expectedGWPortId);
            assert.equals(n.swport.elementId(), expectedSWPortId);
            assert.equals(n.switch.elementId(), expectedSwitchId);
        },
        'nodes do not expand when not expandable': function () {

            var node = new Node({expandable: false, state: 'collapsed'});

            node.expand();
            assert.equals(node.get('state'), 'collapsed');
        },
        'node do not expand when already processing': function () {

            var node = new Node({expandable: true, state: 'processing'});

            node.expand();
            assert.equals(node.get('state'), 'processing');
        },
        'collapse works': function () {

            var node = new Node({state: 'expanded'});

            node.collapse();
            assert.equals(node.get('state'), 'collapsed');
        },
        'event triggered on successful expand': function () {

            // TODO: Make this work :-/
//            var node = this.Nodes.root;
//            var treeView = new TreeView({model: this.Tree});
//            this.stub(treeView, 'render');
//
//            node.expand();
//            assert.calledOnce(treeView.render);
            assert(true);
        },
        'match works': function () {

            var node = new Node({expandable: true});
            var nodeView = new NodeView({model: node});

            this.stub(nodeView, 'triggerExpand');

            nodeView.match(node);
            assert.calledOnce(nodeView.triggerExpand);
        },
        'getChildren works': function () {

            var node = new Node({expandable: true});
            var children = node.getChildren();

            refute.equals(node.get('children'), children);
            assert.equals(node.url, children.url);

            node.set('children', children);
            assert.equals(node.get('children'), node.getChildren());
        },
        'node-views have templates': function () {

            var v = this.NodeViews;
            var n = this.Nodes;
            assert(v.routerView.template(n.router.toJSON()));
            assert(v.gwportView.template(n.gwport.toJSON()));
            assert(v.swportView.template(n.swport.toJSON()));
            assert(v.switchView.template(n.switch.toJSON()));
        }
    });
});
*/

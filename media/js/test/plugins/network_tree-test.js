require(['plugins/network_tree', 'libs/jquery'], function (NetworkTree) {

    var Node = NetworkTree.Node;
    var NodeView = NetworkTree.NodeView;
    var NodeCollection = NetworkTree.NodeCollection;

    buster.testCase('Network tree', {

        setUp: function () {
            this.Nodes = {
                'root': new Node(),
                'router': new Node({pk:1, type:'router'}),
                'gwport': new Node({pk:2, type:'gwport'}),
                'swport': new Node({pk:3, type:'swport'}),
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
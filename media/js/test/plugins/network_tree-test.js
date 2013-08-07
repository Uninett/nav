require(['plugins/network_tree', 'libs/jquery'], function (NetworkTree) {

    var Node = NetworkTree.Node;

    buster.testCase('Network tree', {

        setUp: function () {
            this.Nodes = {
                'root': new Node(),
                'router': new Node({pk:1, type:'router'}),
                'gwport': new Node({pk:2, type:'gwport'}),
                'swport': new Node({pk:3, type:'swport'}),
                'switch': new Node({pk:4, type:'swport', switch_id:1})
            };
        },

        'is defined': function () {
            assert.defined(NetworkTree);
        },

        'test Node urls': function () {

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

        'test Node elementId': function () {

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
        }

    });
});
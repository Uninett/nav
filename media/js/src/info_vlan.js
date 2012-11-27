require(['plugins/graphfetcher', 'libs/jquery'], function (GraphFetcher) {
    $(function () {
        $('.vlangraph').each(function (index, element) {
            var vlanid = $(element).attr('data-vlan');
            var url = '/info/vlan/graph/vlan/' + vlanid;
            var config = {
                'title': "Total active ipv4-addresses on this vlan. This is the stacked values from each prefix."
            };
            new GraphFetcher($(element), url, config);
        });

        $('.prefixgraph').each(function (index, element) {
            var prefixid = $(element).attr('data-prefix');
            var url = '/info/vlan/graph/prefix/' + prefixid;
            var config = {
                'title': "Number of active ip- and mac-addresses on this prefix"
            };
            new GraphFetcher($(element), url, config);
        });

    });
});

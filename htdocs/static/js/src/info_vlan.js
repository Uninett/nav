require(['plugins/graphfetcher', 'libs/jquery'], function (GraphFetcher) {
    $(function () {
        $('.vlangraph').each(function (index, element) {
            var vlanid = $(element).attr('data-vlan');
            var family = $(element).attr('data-family');
            var url = '/search/vlan/graph/vlan/' + vlanid + '/' + family;
            var config = {
                'title': "Total active addresses on this vlan. This is the stacked values from each prefix."
            };
            new GraphFetcher($(element), url, config);
        });

        $('.prefixgraph').each(function (index, element) {
            var prefixid = $(element).attr('data-prefix');
            var url = '/search/vlan/graph/prefix/' + prefixid;
            var config = {
                'title': "Number of active ip- and mac-addresses on this prefix"
            };
            new GraphFetcher($(element), url, config);
        });

    });
});

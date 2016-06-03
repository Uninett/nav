require(['plugins/graphfetcher'], function (GraphFetcher) {
    $(function () {
        $('.vlangraph').each(function (index, element) {
            new GraphFetcher($(element), element.dataset.url);
        });

        $('.prefixgraph').each(function (index, element) {
            new GraphFetcher($(element), element.dataset.url);
        });

    });
});

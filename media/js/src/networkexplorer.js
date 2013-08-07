require(['plugins/network_tree', 'libs/jquery'], function (NetworkTree) {

    function fadeIn(search_form) {
        search_form.fadeTo('normal', 1.0);
    }
    function fadeOut(search_form) {
        search_form.fadeTo('normal', 0.5);
    }
    function submitForm(search_form, working) {
        fadeOut(search_form);
        working.css('visibility', 'visible');

        $.getJSON(
            'search/',
            search_form.serialize()
        )
            .done(function (data) { parseResult(data); })
            .fail(function () { notifyFail('Search failed!'); })
            .always(
                function () {
                    fadeIn(search_form);
                    working.css('visibility', 'hidden');
                }
            );
    }
    function parseResult(data) {
        networkTree.search(data);
    }
    function notifyFail(text) {
        var notify_area = $('#notify_area');
        notify_area.html(
            '<div data-alert class="alert-box">' +
                text +
                '<a href="#" class="close">&times;</a>' +
            '</div>'
        );
    }

    $(document).ready(function () {
        var working = $('#working');
        var search_form = $('#search_form');

        search_form.submit(function (e) {
            e.preventDefault();
            submitForm(search_form, working);
        });

        // Network tree
        var networkTree = new NetworkTree.TreeView({
            model: new NetworkTree.Tree()
        });
        networkTree.model.expand();
    });
});
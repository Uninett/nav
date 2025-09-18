require(['plugins/network_tree'], function (NetworkTree) {

    function fadeIn(search_form) {
        search_form.fadeTo('normal', 1.0);
    }
    function fadeOut(search_form) {
        search_form.fadeTo('normal', 0.5);
    }
    function submitForm(networkTree, search_form, working) {
        fadeOut(search_form);
        working.css('visibility', 'visible');

        $.getJSON(
            'search/',
            search_form.serialize()
        )
            .done(function (data) { parseResult(networkTree, data); })
            .fail(function (response) {
                const errors = response?.responseJSON?.errors;
                if (!errors) {
                    return notifyFail('Search failed!');
                }
                const errorMsg = Object.values(errors)
                    .flat()
                    .join(', ');
                notifyFail(errorMsg);
            })
            .always(
                function () {
                    fadeIn(search_form);
                    working.css('visibility', 'hidden');
                }
            );
    }
    function parseResult(networkTree, data) {
        networkTree.search(data);
    }
    function notifyFail(text) {
        var notify_area = $('#notify_area');
        notify_area.html(
            '<div data-nav-alert class="alert-box error">' +
                text +
                '<a href="#" class="close">&times;</a>' +
            '</div>'
        );
    }

    $(document).ready(function () {
        var working = $('#working');
        var search_form = $('#search-form');
        var networkTree = new NetworkTree.TreeView({
            model: new NetworkTree.Tree()
        });
        search_form.submit(function (e) {
            e.preventDefault();
            submitForm(networkTree, search_form, working);
        });

        networkTree.model.expand();
    });
});

require(['plugins/network_tree','plugins/network_tree' , 'libs/jquery'], function (networkTree) {
    'use strict';

    function fadeIn(search_form) {
        search_form.fadeTo('normal', 1.0);
    }
    function fadeOut(search_form) {
        search_form.fadeTo('normal', 0.25);
    }
    function submitForm(search_form) {
        fadeOut(search_form);

        $.getJSON(
            'search/',
            search_form.serialize()
        )
            .done(function (data) { parseResult(data); })
            .fail(function () { notifyFail('Search failed!'); })
            .always(
                function () {
                    fadeIn(search_form);
                    // TODO: remove gif
                }
            );
    }
    function parseResult(data) {
        console.log(data);
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
        working.css('visibility', 'hidden');

        search_form.submit(function (e) {
            e.preventDefault();
            submitForm(search_form);
        });

        // Network tree
        networkTree.model.expand();
    });
});
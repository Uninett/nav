require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {
    var $inputElement = $('#metricsearchinput'),
        $displayElement = $('.selectedMetric');

    $(function () {
        $inputElement.autocomplete(
            {
                'delay': 300,
                'minLength': 3,
                'source': $inputElement.attr('data-url'),
                'select': handleSelect
            }
        );
    });

    function handleSelect(event, ui) {
        if (ui.item.expandable) {
            $inputElement.autocomplete('search', ui.item.value + '.');
        } else {
            displayGraph(ui.item.value);
        }
    }

    function displayGraph(metric) {
        $displayElement.empty();
        $.get($inputElement.attr('data-renderurl'),
            {'metric': metric},
            function (data) {
                $displayElement.append(
                    $('<p>').text(metric),
                    $('<img>').attr('src', data.url)
                );
            }
        );
    }

});

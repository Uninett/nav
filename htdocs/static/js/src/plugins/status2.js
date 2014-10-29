require([
    'libs-amd/text!resources/status2/navlet-event-row.hbs',
    'moment',
    'libs/handlebars',
    'libs/jquery',
    'status/handlebars-helpers'
    ],
function (RowTemplate, Moment) {

    var dateFormat = "YYYY-MM-DD HH:mm:ss",
        sortField = 'start_time';

    var compiledTemplate = Handlebars.compile(RowTemplate);
    $('body').on('navlet-rendered', function (event, $navlet) {
        /** When a Status2Widget is rendered, make it send a request for data,
         * and listen to refresh events */
        if ($navlet.hasClass('Status2Widget')) {
            sendRequest($navlet);
            if (!isListening($navlet)) {
                $navlet.on('refresh', function () {
                    sendRequest($navlet);
                });
            }
        }
    });

    function isListening($element) {
        /* Returns if we are already listening to the refresh event */
        return $element.data('events') && $element.data('events')['refresh'];
    }

    function sendRequest($navlet) {
        var $table = $navlet.find('table.status2table'),
            url = $table.data('api-url'),
            $tbody = $table.find('tbody'),
            $updateField = $table.find('.last-updated');

        var request = $.get(NAV.urls.status2_api_alerthistory + '?' + url);
        request.done(function (data) {
            renderEvents($tbody, data);
            updateLastUpdated($updateField);
        });
    }

    function renderEvents($container, data) {
        var result, results = data.results;
        $container.empty();
        results.sort(sortBySortField);
        for (var i = 0, l = results.length; i < l; i++) {
            result = results[i];
            $container.append(compiledTemplate(result));
        }
    }

    function updateLastUpdated($field) {
        $field.html(Moment().format(dateFormat));
    }

    function sortBySortField(a, b) {
        var asc = false;
        if (a[sortField] < b[sortField]) {
            return asc ? -1 : 1;
        } else if (a[sortField] > b[sortField]) {
            return asc ? 1 : -1;
        }
        return 0;
    }

});

require([
    'libs-amd/text!resources/status2/navlet-event-row.hbs',
    'moment',
    'libs/handlebars',
    'libs/jquery'
    ],
function (RowTemplate, Moment) {

    var dateFormat = "YYYY-MM-DD HH:mm:ss",
        sortField = 'start_time';

    Handlebars.registerHelper('dateFormat', function(context, block) {
        var f = block.hash.format || dateFormat;
        return Moment(context).format(f);
    });

    var compiledTemplate = Handlebars.compile(RowTemplate);
    $('body').on('navlet-rendered', function (event, navlet) {
        if (navlet.hasClass('Status2Widget')) {
            var $table = navlet.find('table.status2table'),
                url = $table.attr('data-api-url'),
                $tbody = $table.find('tbody'),
                $lastUpdated = $table.find('.last-updated');

            sendRequest($tbody, $lastUpdated, url);
        }
    });

    function sendRequest($container, $updateField, url) {
        var request = $.get(NAV.urls.status2_api_alerthistory + '?' + url);
        request.done(function (data) {
            renderEvents($container, data);
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

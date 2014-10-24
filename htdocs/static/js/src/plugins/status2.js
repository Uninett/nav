require([
    'libs-amd/text!resources/status2/navlet-row.hbs',
    'moment',
    'libs/handlebars',
    'libs/jquery'
    ],
function (RowTemplate, Moment) {

    var dateFormat = "YYYY-MM-DD HH:mm:ss";

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

            var request = $.get(url);
            request.done(function (data) {
                renderEvents($tbody, data);
                updateLastUpdated($lastUpdated);
            });
        }
    });

    function renderEvents($container, data) {
        var result, results = data.results;
        $container.empty();
        for (var i = 0, l = results.length; i < l; i++) {
            result = results[i];
            $container.append(compiledTemplate(result));
        }
    }

    function updateLastUpdated($field) {
        $field.html(Moment().format(dateFormat));
    }

});

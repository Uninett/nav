require([], function () {
    $(function () {
        var $graph = $('.statistics-chart');

        $('#line-chart').click(function () {
            addGraphType('line');
            setActiveButton($(this));
        });

        $('#pie-chart').click(function () {
            addGraphType('pie');
            setActiveButton($(this));
        });

        function setActiveButton($button) {
            $button.parents('ul:first').find('a').removeClass('active');
            $button.addClass('active');
        }

        function addGraphType(type) {
            var src = $graph.attr('src');
            if (src.indexOf('graphType') >= 0) {
                src = src.replace(/graphType=(line|pie)/, 'graphType=' + type);
            } else {
                src += '&graphType=' + type;
            }
            $graph.attr('src', src);
        }
    });
});

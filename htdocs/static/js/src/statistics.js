require(['libs/jquery'], function () {
    $(function () {
        var $graph = $('.statistics-graph');

        $('#line-graph').click(function () {
            addGraphType('line');
            setActiveButton($(this));
        });

        $('#pie-graph').click(function () {
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

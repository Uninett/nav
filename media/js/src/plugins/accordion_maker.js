define(['libs/jquery'], function () {
    function accordionMaker($elements) {
        if ($(window).width() > 640) {
            $elements.show();
        } else {
            $elements.each(function (index, element) {
                var $element = $(element),
                    $content = $element.find('.tabcontent:first'),
                    $active = $element.find('.tabactive:first');

                $element.hide();
                $element.removeClass('tabs').addClass('accordion');
                $content.removeClass('tabcontent').addClass('accordion-content');
                $content.appendTo($active);

                $element.show();
            });

        }
    }

    return accordionMaker;

});

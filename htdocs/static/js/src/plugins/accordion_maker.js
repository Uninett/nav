define([], function () {

    var triggerWidth = 640;  // Width to trigger accordion on

    function accordionMaker($elements) {
        showContent($elements);

        $(window).resize(function () {
            showContent($elements);
        });
    }

    function showContent($elements) {
        if ($(window).width() > triggerWidth && isAccordion($elements)) {
            convertToTabs($elements);
        } else if ($(window).width() < triggerWidth && !isAccordion($elements)) {
            convertToAccordion($elements);
        }
        $elements.show();
    }

    function convertToTabs($elements) {
        $elements.each(function (index, element) {
            var $element = $(element),
                $content = $element.find('.accordion-content:first'),
                $active = $element.find('.tabactive:first');

            $element.hide();
            $element.removeClass('accordion').addClass('tabs');
            $content.removeClass('accordion-content').addClass('tabcontent');
            $content.appendTo($element);
        });
    }

    function convertToAccordion($elements) {
        $elements.each(function (index, element) {
            var $element = $(element),
                $content = $element.find('.tabcontent:first'),
                $active = $element.find('.tabactive:first');

            $element.hide();
            $element.removeClass('tabs').addClass('accordion');
            $content.removeClass('tabcontent').addClass('accordion-content');
            $content.appendTo($active);
        });

    }

    function isAccordion($elements) {
        return $elements.hasClass('accordion');
    }

    return accordionMaker;

});

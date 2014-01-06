require(['plugins/accordion_maker', 'default', 'libs/foundation.min', 'libs/select2.min'], function (accordionMaker) {
    $(function () {
        $(document).foundation();   // Apply foundation javascript on load
        accordionMaker($('.tabs')); // Apply accordionmaker for tabs
        $('select.select2').select2();

        var $megadrop = $('#megadrop'),
            $megadroptoggler = $('#megadroptoggler'),
            $caret = $megadroptoggler.find('i');
        $megadroptoggler.click(function () {
            $megadrop.slideToggle(300, function () {
                if ($(this).is(':hidden')) {
                    $caret.removeClass('fa-caret-up').addClass('fa-caret-down');
                } else {
                    $caret.removeClass('fa-caret-down').addClass('fa-caret-up');
                }
            });
        });
    });
});

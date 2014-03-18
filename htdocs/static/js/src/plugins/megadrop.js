/* Javascript for MegaDrop functionality in NAV */
require(['libs/jquery'], function () {
    $(function () {
        var megadropSelector = 'megadrop',
            megadropTogglerSelector = 'megadroptoggler',
            $megadrop = $(document.getElementById(megadropSelector)),
            $megadroptoggler = $(document.getElementById(megadropTogglerSelector)),
            $caret = $megadroptoggler.find('i'),
            caretDownClass = 'fa-caret-down',
            caretUpClass = 'fa-caret-up',
            slidespeed = 300;

        /* Toggle megadrop on click */
        $megadroptoggler.click(function () {
            if ($megadrop.is(':visible')) {
                $megadrop.slideUp(slidespeed, function () {
                    $caret.removeClass(caretUpClass).addClass(caretDownClass);
                });
            } else {
                $megadrop.slideDown(slidespeed, function () {
                    $caret.removeClass(caretDownClass).addClass(caretUpClass);
                });
            }
        });

    });
});

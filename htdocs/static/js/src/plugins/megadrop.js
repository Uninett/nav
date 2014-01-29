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

        function hideMegaDrop() {
            $megadrop.slideUp(slidespeed, function () {
                $caret.removeClass(caretUpClass).addClass(caretDownClass);
            });
        }

        function inMegadrop(element) {
            var $element = $(element);
            return $element.prop('id') === megadropSelector || $element.parents('#' + megadropSelector).length;
        }

        function inMegadropToggler(element) {
            var $element = $(element);
            return $element.prop('id') === megadropTogglerSelector || $element.parents('#' + megadropTogglerSelector).length;
        }

        /* Show megadrop on mouseover */
        $megadroptoggler.mouseover(function () {
            $megadrop.slideDown(slidespeed, function () {
                $caret.removeClass(caretDownClass).addClass(caretUpClass);
            });
        });

        /* Hide megadrop when mouse leaves link and not enters megadrop */
        $megadroptoggler.mouseleave(function (event) {
            if (!inMegadrop(event.relatedTarget)) {
                hideMegaDrop();
            }
        });

        /* Hide megadrop when mouse leaves megadrop and not enters toggler */
        $megadrop.mouseleave(function (event) {
            if (!inMegadropToggler(event.relatedTarget)) {
                hideMegaDrop();
            }
        });
    });
});

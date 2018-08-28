/* Javascript for MegaDrop functionality in NAV */
require([], function () {
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

        function showMegaDrop() {
            $megadrop.slideDown(slidespeed, function () {
                $caret.removeClass(caretDownClass).addClass(caretUpClass);
            });
        }

        $megadroptoggler.click(function () {
            if ($megadrop.is(':visible')) {
                hideMegaDrop();
            } else {
                showMegaDrop();
            }
        });

        /*
            Hide megadrop when clicking outside it. See special case for
            top-bar dropdowns below
        */
        $(document).click(function (event) {
            if ($megadrop.is(":visible")) {
                var $target = $(event.target),
                    clickIsOutsideMegadrop = $target.parents('#' + megadropSelector).length <= 0,
                    clickIsOnToggler = $target[0] === $megadroptoggler[0] || $target.parent()[0] === $megadroptoggler[0];

                if (clickIsOutsideMegadrop && !clickIsOnToggler) {
                    hideMegaDrop();
                }
            }
        });

        /* Special case for top bar dropdown menus (event does not propagate to document) */
        $('.top-bar .has-dropdown').click(function () {
            if ($megadrop.is(":visible")) {
                hideMegaDrop();
            }
        });

    });
});

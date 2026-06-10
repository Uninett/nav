/* Javascript for MegaDrop functionality in NAV */
require([], function () {
    $(function () {
        var megadropSelector = 'megadrop',
            megadropTogglerSelector = 'megadroptoggler',
            mystuffTogglerSelector = 'mystufftoggler',
            $megadrop = $(document.getElementById(megadropSelector)),
            $megadroptoggler = $(document.getElementById(megadropTogglerSelector)),
            $mystufftoggler = $(document.getElementById(mystuffTogglerSelector)),
            $mystuffItem = $mystufftoggler.closest('li'),
            $caret = $megadroptoggler.find('i'),
            caretDownClass = 'fa-caret-down',
            caretUpClass = 'fa-caret-up',
            slidespeed = 300,
            mystuffIsOpen = false;

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

        function hideMystuff() {
            $mystuffItem.removeClass('open');
            $mystufftoggler[0].blur();
            mystuffIsOpen = false;
        }

        function showMystuff() {
            $mystuffItem.addClass('open');
            mystuffIsOpen = true;
        }

        $megadroptoggler.on('click', function () {
            if ($megadrop.is(':visible')) {
                hideMegaDrop();
            } else {
                showMegaDrop();
            }
        });

        $mystufftoggler.on('click', function (e) {
            if (mystuffIsOpen) {
                hideMystuff();
            } else {
                hideMegaDrop();
                showMystuff();
            }
            e.stopPropagation();
        });

        /*
            Hide megadrop when clicking outside it. See special case for
            top-bar dropdowns below
        */
        $(document).on('click', function (event) {
            const $target = $(event.target);
            if ($megadrop.is(":visible")) {
                const clickIsOutsideMegadrop = $target.parents('#' + megadropSelector).length <= 0,
                    clickIsOnToggler = $target[0] === $megadroptoggler[0] || $target.parent()[0] === $megadroptoggler[0];

                if (clickIsOutsideMegadrop && !clickIsOnToggler) {
                    hideMegaDrop();
                }
            }
            if (mystuffIsOpen) {
                const clickIsOutsideMystuff = $target.closest('#' + mystuffTogglerSelector).length === 0
                        && $target.closest('.has-dropdown').length === 0;
                if (clickIsOutsideMystuff) {
                    hideMystuff();
                }
            }
        });

        /* Special case for top bar dropdown menus (event does not propagate to document) */
        $('.top-bar .has-dropdown').on('click', function () {
            if ($megadrop.is(":visible")) {
                hideMegaDrop();
            }
        });

    });
});

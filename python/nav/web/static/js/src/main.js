define('jquery', [], function() {
    return jQuery;
});

require([
    'plugins/accordion_maker',
    'libs/foundation.min',
    'libs/select2.min',
    'plugins/megadrop',
    'plugins/popover',
    'plugins/tooltip',
    'libs/underscore'
], function (accordionMaker) {
    /** Enable slash to navigate to search, whereas escape removes focus from search */
    function addSearchFocusHandlers() {
        var $searchInput = $('#query');

        // Listen to keypress for slash, go to search if pressed.
        $(document).keypress(function (event) {
            if (event.keyCode === 47) {
                event.preventDefault();
                $searchInput.focus();
            }
        });

        // Remove focus when escape is pressed
        $searchInput.keyup(function (event) {
            if (event.keyCode === 27) {
                $searchInput.blur();
            }
        });

    }

    function refreshSession() {
        $.post(NAV.urls.refresh_session);
    }


    /** Should we put polyfills here maybe? Lets try */
    $.fn.serializeObject = function()
    {
        var o = {};
        var a = this.serializeArray();
        $.each(a, function() {
            if (o[this.name] !== undefined) {
                if (!o[this.name].push) {
                    o[this.name] = [o[this.name]];
                }
                o[this.name].push(this.value || '');
            } else {
                o[this.name] = this.value || '';
            }
        });
        return o;
    };

    function addTopbarHandlers() {
        // Toggle topbar on small screens
        $('.top-bar').on('click', '.toggle-topbar', function (e) {
            e.preventDefault();
            const $this = $(this);
            const $topbar = $this.closest('.top-bar');
            $topbar.toggleClass('expanded');
        });
        // Cleanup topbar if we resize to large screen
        $(window).on('resize', _.throttle(function () {
            if (window.matchMedia('(min-width: 40em)').matches) {
                $('.top-bar').removeClass('expanded');
            }
        }, 200));
    }

    $(function () {
        /* Add redirect to login on AJAX-requests if session has timed out */
        $(document).ajaxError(function (event, request) {
            if (request.status === 401) {
                window.location = '/index/login/?origin=' + encodeURIComponent(window.location.href);
            }
        });

        $(document).foundation();   // Apply foundation javascript on load
        accordionMaker($('.tabs')); // Apply accordionmaker for tabs
        $('select.select2').select2();

        // addSearchFocusHandlers();  Fix this to not grab every / before activating
        addTopbarHandlers();

        // Refresh session on page load and then periodically
        var ten_minutes = 10 * 60 * 1000;
        refreshSession();
        setInterval(refreshSession, ten_minutes);
    });
});

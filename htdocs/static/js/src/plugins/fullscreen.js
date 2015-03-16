/**
 * Big thanks to https://developer.mozilla.org/en-US/docs/Web/Guide/API/DOM/Using_full_screen_mode
 *
 * NOTE: Fullscreen requests need to be called from within an event handler
 * or otherwise they will be denied.
 *
 * Usage:
 * var map = $(mapSelector),
 * toggler = fullscreen.createFullscreenToggler(map).appendTo(map);
 */
define([], function () {

    function toggleFullscreen(element) {
        /** Toggle fullscreen mode for an element or document if none */
        if (isFullscreenSupported()) {
            if (isInFullscreen()) {
                exitFullscreen();
            } else {
                requestFullscreen(element);
            }
        } else {
            console.log("Fullscreen is not supported by this browser");
        }
    }

    function isFullscreenSupported() {
        /** Returns if fullscreen mode is supported in this browser or not */
        return document.fullscreenEnabled ||
            document.webkitFullscreenEnabled ||
            document.mozFullScreenEnabled ||
            document.msFullscreenEnabled || false;
    }

    function isInFullscreen() {
        /** Returns if we are in fullscreen mode or not */
        return document.fullscreenElement ||
            document.mozFullScreenElement ||
            document.webkitFullscreenElement ||
            document.msFullscreenElement || false;
    }

    function exitFullscreen() {
        /** Exit fullscreen mode */
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }

    function requestFullscreen(element) {
        /** Request fullscreen for this element or the document if none */
        element = element || document.documentElement;
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
        }
    }

    /**
     * Example fullscreentoggler. Adjust CSS as needed. Remember to
     * add it to document.
     * @param {HTMLElement} [element] Optional element to trigger fullscreen on
     */
    function createFullscreenToggler(element) {
        var toggler = $('<button class="tiny"><i class="fa fa-arrows-alt fa-lg"></i></button>');
        toggler.css({
            'position': 'absolute',
            'right': '30px',
            'top': '10px',
            'z-index': 999
        });

        if (typeof element !== 'undefined') {
            if (element instanceof jQuery) {
                element = element[0];
            }
            toggler.on('click', function() {
                toggleFullscreen(element);
            });
        }
        return toggler;
    }


    return {
        'toggleFullscreen': toggleFullscreen,
        'isFullscreenSupported': isFullscreenSupported,
        'isInFullscreen': isInFullscreen,
        'exitFullscreen': exitFullscreen,
        'requestFullscreen': requestFullscreen,
        'createFullscreenToggler': createFullscreenToggler
    };

});

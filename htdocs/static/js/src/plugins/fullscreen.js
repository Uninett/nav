/**
 * Big thanks to https://developer.mozilla.org/en-US/docs/Web/Guide/API/DOM/Using_full_screen_mode
 *
 * NOTE: Fullscreen requests need to be called from within an event handler
 * or otherwise they will be denied.
 *
 * Written to be jQuery independent
 *
 * Usage:
 * var map = document.getElementById(mapSelector),
 * toggler = fullscreen.createFullscreenToggler(map, true);
 *
 * Overwrite default style:
 * var toggler = fullscreen.createFullscreenToggler(map, true);
 * toggler.style.right = 20px;
 * toggler.style['background-color'] = 'black';
 */
define([], function () {

    /**
     * Toggle fullscreen mode for an element or document if none
     * @param {HTMLElement} [element] Element to toggle fullscreen for
     */
    function toggleFullscreen(element) {
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

    /**
     * Returns if fullscreen mode is supported in this browser or not
     * @returns {boolean}
     */
    function isFullscreenSupported() {
        return document.fullscreenEnabled ||
            document.webkitFullscreenEnabled ||
            document.mozFullScreenEnabled ||
            document.msFullscreenEnabled || false;
    }

    /**
     * Returns if we are in fullscreen mode or not
     * @returns {boolean}
     */
    function isInFullscreen() {
        return document.fullscreenElement ||
            document.mozFullScreenElement ||
            document.webkitFullscreenElement ||
            document.msFullscreenElement || false;
    }

    /**
     * Exit fullscreen mode
     */
    function exitFullscreen() {
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

    /**
     * Request fullscreen for this element or the document if none
     * @param {HTMLElement} [element] Element to toggle fullscreen for
     */
    function requestFullscreen(element) {
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
     * Example fullscreentoggler. Adjust styles as needed. Remember to
     * add it to document, or set append flag.
     * @param {HTMLElement} [element] Optional element to trigger fullscreen on
     * @param {boolean} [append] Append trigger to element or not, default false
     * @returns {HTMLElement}
     */
    function createFullscreenToggler(element, append) {
        element.style.position = 'relative';
        var button = document.createElement('button'),
            icon = document.createElement('i');
        button.className = 'tiny';
        icon.className = 'fa fa-arrows-alt fa-lg';
        button.appendChild(icon);

        button.style.position = 'absolute';
        button.style.right = '10px';
        button.style.top = '10px';
        button.style['z-index'] = 999;

        if (typeof element !== 'undefined') {
            if (element instanceof jQuery) {
                element = element[0];
            }
            button.onclick = function() {
                toggleFullscreen(element);
            };
        }

        if (append) {
            element.appendChild(button);
        }

        return button;
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

/**
 * CSRF utility functions for AJAX requests.
 * Django's recommended approach is to read the token from the cookie.
 * See: https://docs.djangoproject.com/en/5.0/howto/csrf/
 *
 * This module works as both a standalone script (exposes window.getCsrfToken)
 * and as a RequireJS module for compatibility with existing code.
 */
(function(root) {
    function getCsrfToken() {
        const name = 'csrftoken=';
        if (document.cookie && document.cookie !== '') {
            for (const part of document.cookie.split(';')) {
                const cookie = part.trim();
                if (cookie.startsWith(name)) {
                    return decodeURIComponent(cookie.substring(name.length));
                }
            }
        }
        return null;
    }

    // Expose globally for standalone usage
    root.getCsrfToken = getCsrfToken;

    // Also define as RequireJS module if available
    if (typeof define === 'function' && define.amd) {
        define([], function () {
            return {
                getCsrfToken: getCsrfToken
            };
        });
    }
})(window);

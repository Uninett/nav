/**
 * CSRF utility functions for AJAX requests.
 * Django's recommended approach is to read the token from the cookie.
 * See: https://docs.djangoproject.com/en/5.0/howto/csrf/
 */
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

define([], function () {
    return {
        getCsrfToken: getCsrfToken
    };
});

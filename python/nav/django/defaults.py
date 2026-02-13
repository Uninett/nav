PUBLIC_URLS = [
    '/api/',  # No auth/different auth system
    '/doc/',  # No auth/different auth system
    '/about/',
    '/index/login/',
    '/index/audit-logging-modal/',
    '/refresh_session',
    '/accounts/login/',
    '/accounts/2fa/authenticate/',
]
NAV_LOGIN_URL = '/index/login/'
ALLAUTH_LOGIN_URL = '/accounts/login/'

LOGIN_URL = ALLAUTH_LOGIN_URL

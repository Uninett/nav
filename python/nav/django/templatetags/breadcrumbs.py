from django import template
from django.urls import reverse

register = template.Library()

BASE_CRUMB = ('Home', reverse('webfront-index'))

# Account-related Breadcrumbs
BASE_ACCOUNT_CRUMB = ('Account', reverse('webfront-preferences'))
CURRENT_PATH = ''
ACCOUNTS_BREADCRUMB_MAP = {
    reverse('webfront-preferences'): [BASE_ACCOUNT_CRUMB],
    reverse('account_change_password'): [
        BASE_ACCOUNT_CRUMB,
        ('Change Password', CURRENT_PATH),
    ],
    reverse('account_reauthenticate'): [
        BASE_ACCOUNT_CRUMB,
        ('Re-authenticate', CURRENT_PATH),
    ],
    reverse('socialaccount_connections'): [
        BASE_ACCOUNT_CRUMB,
        ('Account Connections', CURRENT_PATH),
    ],
}

# Combine all breadcrumb mappings
BREADCRUMB_MAP = {
    **ACCOUNTS_BREADCRUMB_MAP,
}

# 2FA Breadcrumbs
TWO_FACTOR_AUTH_CRUMB = [
    BASE_ACCOUNT_CRUMB,
    ('Two-Factor Authentication', CURRENT_PATH),
]


@register.filter
def to_breadcrumbs(path):
    """
    Generate breadcrumb navigation from a given URL path.

    :param path: The URL path (e.g., "/section/subsection/page/").
    :type path: str
    :return: A list of tuples where each tuple contains the name and URL
        of each breadcrumb.
    :rtype: list
    """
    # Remove leading and trailing slashes and split the path
    path = clean_path(path)
    if path in BREADCRUMB_MAP:
        crumbs = [BASE_CRUMB] + BREADCRUMB_MAP[path]
        return crumbs

    if path.startswith(reverse('mfa_index')):
        return [BASE_CRUMB] + TWO_FACTOR_AUTH_CRUMB

    return [BASE_CRUMB]


def clean_path(path):
    """Cleans the path by removing query parameters."""
    path = path.split('?', 1)[0]
    return path

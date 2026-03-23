from functools import cache

from django import template
from django.urls import reverse

register = template.Library()


@cache
def _get_breadcrumb_config():
    """Build breadcrumb configuration on first use.

    Deferred to avoid calling reverse() at module import time, which forces
    all URL configs and their views to be loaded eagerly.
    """
    base_crumb = ('Home', reverse('webfront-index'))
    base_account_crumb = ('Account', reverse('webfront-preferences'))

    breadcrumb_map = {
        reverse('webfront-preferences'): [base_account_crumb],
        reverse('account_change_password'): [
            base_account_crumb,
            ('Change Password', ''),
        ],
        reverse('account_reauthenticate'): [
            base_account_crumb,
            ('Re-authenticate', ''),
        ],
        reverse('socialaccount_connections'): [
            base_account_crumb,
            ('Account Connections', ''),
        ],
    }

    two_factor_auth_crumb = [
        base_account_crumb,
        ('Two-Factor Authentication', ''),
    ]

    mfa_prefix = reverse('mfa_index')

    return base_crumb, breadcrumb_map, two_factor_auth_crumb, mfa_prefix


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
    base_crumb, breadcrumb_map, two_factor_auth_crumb, mfa_prefix = (
        _get_breadcrumb_config()
    )

    path = clean_path(path)
    if path in breadcrumb_map:
        return [base_crumb] + breadcrumb_map[path]

    if path.startswith(mfa_prefix):
        return [base_crumb] + two_factor_auth_crumb

    return [base_crumb]


def clean_path(path):
    """Cleans the path by removing query parameters."""
    path = path.split('?', 1)[0]
    return path

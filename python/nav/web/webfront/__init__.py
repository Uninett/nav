"""NAV web common package."""

DEFAULT_WIDGET_COLUMNS = 2

from nav.models import PREFERENCE_KEY_WIDGET_COLUMNS

def get_widget_columns(account):
    """Get the preference for widget columns"""
    return int(account.preferences.get(PREFERENCE_KEY_WIDGET_COLUMNS,
                                       DEFAULT_WIDGET_COLUMNS))

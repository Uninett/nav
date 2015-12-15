"""NAV web common package."""

DEFAULT_WIDGET_COLUMNS = 2

def get_widget_columns(account):
    """Get the preference for widget columns"""
    return int(account.preferences.get(account.PREFERENCE_KEY_WIDGET_COLUMNS,
                                       DEFAULT_WIDGET_COLUMNS))

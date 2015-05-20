"""NAV web common package."""
from nav.models.profiles import AccountProperty

DEFAULT_WIDGET_COLUMNS = 2
WIDGET_COLUMNS_PROPERTY = 'widget_columns'

def get_widget_columns(account):
    """Get the preference for widget columns"""
    try:
        return int(account.properties.get(
            property=WIDGET_COLUMNS_PROPERTY).value)
    except AccountProperty.DoesNotExist:
        return DEFAULT_WIDGET_COLUMNS

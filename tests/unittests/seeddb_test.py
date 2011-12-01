from django.core.urlresolvers import reverse

def test_usage_edit_url_should_allow_slashes():
    assert reverse('seeddb-usage-edit', args=('TEST/SLASH',))

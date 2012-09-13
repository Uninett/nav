from mock import patch, Mock

@patch("nav.models.manage.Organization.objects.all")
@patch("nav.models.manage.Category.objects.all")
def test_module_section_should_not_crash_on_empty_module_name(*args):
    from nav.web.status.sections import ModuleSection
    prefs = Mock()
    prefs.fetched_categories = prefs.fetched_organizations = []
    prefs.states = ''

    alert = Mock()
    alert.netbox = Mock(sysname=u"foo")
    alert.module_name = u""

    m = ModuleSection(prefs)
    m.fetch_history([alert])
    assert m.history

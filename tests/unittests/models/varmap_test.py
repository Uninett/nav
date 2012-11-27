from nav.models.event import EventQueue as Event

def test_setting_varmap_on_new_event_should_not_raise():
    event = Event()
    varmap = dict(foo='bar')
    event.varmap = varmap
    assert event.varmap == varmap

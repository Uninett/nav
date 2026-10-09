from django.test import TestCase

from nav.models.event import AlertType, EventType
from nav.snmptrapd.handlers import linkupdown, ups


class EventTypeVerificationTest(TestCase):
    """The handlers' verify functions ensure their event/alert types exist."""

    def _assert_types(self, eventtypeid, alerttypes):
        event_type = EventType.objects.get(id=eventtypeid)
        names = set(
            AlertType.objects.filter(event_type=event_type).values_list(
                'name', flat=True
            )
        )
        assert names >= set(alerttypes)

    def test_when_linkstate_types_missing_then_verify_creates_them(self):
        EventType.objects.filter(id='linkState').delete()
        linkupdown.verify_event_type()
        self._assert_types('linkState', ('linkUp', 'linkDown'))

    def test_when_ups_types_missing_then_verify_creates_them(self):
        EventType.objects.filter(id='upsPowerState').delete()
        ups.verifyEventtype()
        self._assert_types('upsPowerState', ('upsOnBatteryPower', 'upsOnUtilityPower'))

    def test_when_verify_runs_twice_then_it_should_not_duplicate_types(self):
        linkupdown.verify_event_type()
        before = AlertType.objects.filter(event_type='linkState').count()
        linkupdown.verify_event_type()
        after = AlertType.objects.filter(event_type='linkState').count()
        assert after == before

from unittest import TestCase
from datetime import datetime
from mock import Mock

from nav.models.profiles import AlertSubscription
from nav.alertengine.base import alert_should_be_ignored

class HandleQueuedAlertsTest(TestCase):
    def test_alert_should_not_be_ignored_on_invalid_subscription(self):
        now = datetime.now()
        qd_alert = Mock()
        qd_alert.alert.history.end_time = datetime(2010, 1, 1, 0, 0, 0)

        self.assertFalse(alert_should_be_ignored(qd_alert, None, now))

    def test_alert_should_be_ignored_when_subscription_says_so(self):
        before = datetime(2010, 1, 1, 23, 59, 0)
        later = datetime(2010, 1, 2, 0, 0, 0)

        qd_alert = Mock()
        qd_alert.alert.history.end_time = before

        sub = Mock()
        sub.ignored_resolved_alerts = True
        sub.type = AlertSubscription.DAILY

        self.assertTrue(alert_should_be_ignored(qd_alert, sub, later))

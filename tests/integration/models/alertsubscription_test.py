from datetime import datetime
from nav.models.profiles import (
    Account,
    AccountAlertQueue,
    AlertAddress,
    AlertProfile,
    AlertSender,
    AlertSubscription,
    FilterGroup,
    TimePeriod
)
from nav.models.event import AlertQueue, Subsystem
import pytest


def test_delete_alert_subscription(db, alert, alertsub):
    account_queue = AccountAlertQueue(alert=alert, subscription=alertsub)
    account_queue.save()
    alertsub.delete()
    assert not AccountAlertQueue.objects.filter(pk=account_queue.pk).exists()
    assert not AlertQueue.objects.filter(pk=alert.pk).exists()


@pytest.fixture
def account():
    return Account.objects.get(pk=Account.ADMIN_ACCOUNT)


@pytest.fixture
def alert_address(account):
    addr = AlertAddress(
        account=account,
        type=AlertSender.objects.get(name=AlertSender.SMS),
    )
    addr.save()
    yield addr
    if addr.pk:
        addr.delete()


@pytest.fixture
def alert_profile(account):
    profile = AlertProfile(account=account)
    profile.save()
    yield profile
    if profile.pk:
        profile.delete()


@pytest.fixture
def time_period(alert_profile):
    time_period = TimePeriod(profile=alert_profile)
    time_period.save()
    yield time_period
    if time_period.pk:
        time_period.delete()


@pytest.fixture
def alertsub(alert_address, time_period):
    alertsub = AlertSubscription(
        alert_address=alert_address,
        time_period=time_period,
        filter_group=FilterGroup.objects.first()
    )
    alertsub.save()
    yield alertsub
    if alertsub.pk:
        alertsub.delete()


@pytest.fixture
def alert():
    alert = AlertQueue(source=Subsystem.objects.first(), time=datetime.now(),
                       value=1, severity=1)
    alert.save()
    yield alert
    if alert.pk:
        alert.delete()

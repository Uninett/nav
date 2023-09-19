from datetime import datetime

from nav.alertengine.dispatchers import InvalidAlertAddressError
from nav.models.profiles import (
    Account,
    AccountAlertQueue,
    AlertAddress,
    AlertProfile,
    AlertSender,
    AlertSubscription,
    FilterGroup,
    TimePeriod,
)
from nav.models.event import AlertQueue, Subsystem

import pytest


def test_delete_alert_subscription(db, alert, alertsub, account_alert_queue):
    alertsub.delete()
    assert not AccountAlertQueue.objects.filter(pk=account_alert_queue.pk).exists()
    assert not AlertQueue.objects.filter(pk=alert.pk).exists()


def test_sending_alert_to_alert_address_with_empty_address_will_raise_error(
    db, alert_address, alert, alertsub
):
    with pytest.raises(InvalidAlertAddressError):
        alert_address.send(alert, alertsub)


def test_sending_alert_to_alert_address_with_invalid_address_will_raise_error(
    db, alert_address, alert, alertsub
):
    alert_address.address = "abc"
    alert_address.save()
    with pytest.raises(InvalidAlertAddressError):
        alert_address.send(alert, alertsub)


def test_sending_alert_to_alert_address_with_invalid_address_will_delete_alert_and_fail(
    db, alert, account_alert_queue
):
    assert not account_alert_queue.send()
    assert not AlertQueue.objects.filter(pk=alert.pk).exists()


@pytest.fixture
def alert_address(db, admin_account):
    addr = AlertAddress(
        account=admin_account,
        type=AlertSender.objects.get(name=AlertSender.SMS),
    )
    addr.save()
    yield addr
    if addr.pk:
        addr.delete()


@pytest.fixture
def alert_profile(db, admin_account):
    profile = AlertProfile(account=admin_account)
    profile.save()
    yield profile
    if profile.pk:
        profile.delete()


@pytest.fixture
def time_period(db, alert_profile):
    time_period = TimePeriod(profile=alert_profile)
    time_period.save()
    yield time_period
    if time_period.pk:
        time_period.delete()


@pytest.fixture
def alertsub(db, alert_address, time_period):
    alertsub = AlertSubscription(
        alert_address=alert_address,
        time_period=time_period,
        filter_group=FilterGroup.objects.first(),
    )
    alertsub.save()
    yield alertsub
    if alertsub.pk:
        alertsub.delete()


@pytest.fixture
def alert(db):
    alert = AlertQueue(
        source=Subsystem.objects.first(), time=datetime.now(), value=1, severity=3
    )
    alert.save()
    yield alert
    if alert.pk:
        alert.delete()


@pytest.fixture
def account_alert_queue(db, alert, alertsub):
    account_queue = AccountAlertQueue(alert=alert, subscription=alertsub)
    account_queue.save()
    yield account_queue
    if account_queue.pk:
        account_queue.delete()

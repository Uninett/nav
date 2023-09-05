from datetime import datetime
import logging
from mock import patch

from nav.alertengine.base import clear_blacklisted_status_of_alert_senders
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


def test_sending_alert_to_alert_address_with_invalid_address_will_raise_error(
    db, alert_address, alert, alertsub
):
    with pytest.raises(InvalidAlertAddressError):
        alert_address.send(alert, alertsub)


def test_sending_alert_to_alert_address_with_invalid_address_will_delete_alert_and_fail(
    db, alert, account_alert_queue
):
    assert not account_alert_queue.send()
    assert not AlertQueue.objects.filter(pk=alert.pk).exists()


def test_sending_alert_via_blacklisted_sender_will_fail_but_not_delete_alert(
    db, alert, alert_address, account_alert_queue
):
    alert_address.address = "47474747"
    alert_address.save()
    alert_address.type.blacklisted_reason = "This has been blacklisted because of x."
    alert_address.type.save()
    assert not account_alert_queue.send()
    assert AlertQueue.objects.filter(pk=alert.pk).exists()


@patch("nav.alertengine.dispatchers.sms_dispatcher.Sms.send")
def test_error_when_sending_alert_will_blacklist_sender(
    mocked_send_function, db, alert_address, account_alert_queue
):
    exception_reason = "Exception reason"
    mocked_send_function.side_effect = ValueError(exception_reason)
    alert_address.address = "47474747"
    alert_address.save()

    assert not account_alert_queue.send()
    assert alert_address.type.blacklisted_reason == exception_reason


def test_clearing_blacklisted_status_of_alert_senders_will_succeed(db, alert_sender):
    alert_sender.blacklisted_reason = "This has been blacklisted because of x."
    clear_blacklisted_status_of_alert_senders()
    alert_sender.refresh_from_db()

    assert not alert_sender.blacklisted_reason


@pytest.fixture
def account():
    return Account.objects.get(pk=Account.ADMIN_ACCOUNT)


@pytest.fixture
def alert_address(account, alert_sender):
    addr = AlertAddress(
        account=account,
        type=alert_sender,
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
        filter_group=FilterGroup.objects.first(),
    )
    alertsub.save()
    yield alertsub
    if alertsub.pk:
        alertsub.delete()


@pytest.fixture
def alert():
    alert = AlertQueue(
        source=Subsystem.objects.first(), time=datetime.now(), value=1, severity=3
    )
    alert.save()
    yield alert
    if alert.pk:
        alert.delete()


@pytest.fixture
def account_alert_queue(alert, alertsub):
    account_queue = AccountAlertQueue(alert=alert, subscription=alertsub)
    account_queue.save()
    yield account_queue
    if account_queue.pk:
        account_queue.delete()


@pytest.fixture
def alert_sender(db):
    alert_sender = AlertSender.objects.get(name=AlertSender.SMS)
    yield alert_sender
    if alert_sender.pk:
        alert_sender.blacklisted_reason = None
        alert_sender.save()

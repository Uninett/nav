# -*- coding: utf-8 -*-
from random import randint

from mock import MagicMock, patch
import pytest

from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.encoding import smart_str
from nav.models.profiles import (
    AlertAddress,
    AlertPreference,
    AlertProfile,
    AlertSender,
    AlertSubscription,
    Expression,
    Filter,
    FilterGroup,
    MatchField,
    Operator,
    TimePeriod,
)
from nav.web.alertprofiles.views import set_active_profile
from nav.web.auth.utils import set_account


@pytest.mark.parametrize(
    "view",
    [
        'alertprofiles-overview',
        'alertprofiles-profile',
        'alertprofiles-profile-new',
        'alertprofiles-sms',
        'alertprofiles-address',
        'alertprofiles-address-new',
        'alertprofiles-filters',
        'alertprofiles-filters-new',
        'alertprofiles-filter_groups',
        'alertprofiles-filter_groups-new',
        'alertprofiles-matchfields',
        'alertprofiles-matchfields-new',
        'alertprofiles-permissions',
    ],
)
def test_alertprofiles_view(client, view):
    """Simple GET tests for various non-modifying alertprofiles views"""
    url = reverse(view)
    response = client.get(url)
    assert "admin" in smart_str(response.content)


class TestsOverview:
    def test_show_active_profile(self, db, client, activated_dummy_profile):
        response = client.get(reverse('alertprofiles-overview'))

        assert response.status_code == 200
        assert activated_dummy_profile.name in smart_str(response.content)

    def test_when_no_active_profile_is_set_show_message(self, db, client):
        response = client.get(reverse('alertprofiles-overview'))

        assert response.status_code == 200
        assert "There is no active profile set" in smart_str(response.content)

    def test_show_subscriptions(
        self,
        db,
        client,
        dummy_alert_address,
        dummy_filter_group,
        dummy_alert_subscription,
    ):
        response = client.get(reverse('alertprofiles-overview'))

        assert response.status_code == 200
        assert dummy_alert_address.address in smart_str(response.content)
        assert str(dummy_filter_group) in smart_str(response.content)

    def test_should_include_modal_trigger(self, client):
        url = reverse('alertprofiles-overview')
        modal_url = reverse('alertprofiles-groups-and-permissions')
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}"' in smart_str(response.content)

    def test_should_render_permissions_modal(self, client):
        url = reverse('alertprofiles-groups-and-permissions')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="groups-and-permissions"' in smart_str(response.content)


class TestsAlertProfiles:
    def test_profile_with_nonascii_name_should_be_saved(self, db, admin_account):
        factory = RequestFactory()
        request = factory.get(reverse('alertprofiles-profile-save'))
        request.session = MagicMock()
        set_account(request, admin_account)
        profile = AlertProfile(account=admin_account, name='ÆØÅ')
        profile.save()

        assert set_active_profile(request, profile) is None

    def test_show_non_existent_profile(self, db, client):
        last_alert_profile_id = getattr(AlertProfile.objects.last(), "pk", 0)
        response = client.get(
            path=reverse(
                'alertprofiles-profile-detail', args=(last_alert_profile_id + 1,)
            ),
            follow=True,
        )

        assert response.status_code == 200
        assert "The requested profile does not exist." in smart_str(response.content)

    def test_alertprofiles_save_profile(self, db, client):
        url = reverse('alertprofiles-profile-save')
        profile_name = 'Catch 22'

        response = client.post(
            url,
            follow=True,
            data={
                'name': profile_name,
                'daily_dispatch_time': '08:00',
                'weekly_dispatch_time': '08:00',
                'weekly_dispatch_day': AlertProfile.MONDAY,
            },
        )

        assert response.status_code == 200
        assert "Saved profile" in smart_str(response.content)
        assert AlertProfile.objects.filter(name=profile_name).count() > 0

    @patch("nav.web.alertprofiles.views.read_time_period_templates")
    def test_alertprofiles_save_profile_with_time_period_template(
        self, read_time_period_templates, db, client
    ):
        read_time_period_templates.return_value = {
            'abc': {
                'all_week': {'period_1': '22:00'},
                'weekdays': {'period_1': '08:00', 'period_2': '16:00'},
                'weekends': {'period_1': '08:00'},
            }
        }

        url = reverse('alertprofiles-profile-save')
        profile_name = 'Catch 22'

        response = client.post(
            url,
            follow=True,
            data={
                'name': profile_name,
                'daily_dispatch_time': '08:00',
                'weekly_dispatch_time': '08:00',
                'weekly_dispatch_day': AlertProfile.MONDAY,
                'template': 'abc',
            },
        )

        assert response.status_code == 200
        assert "Saved profile" in smart_str(response.content)
        assert TimePeriod.objects.filter(
            profile__name=profile_name,
            start="22:00",
            valid_during=TimePeriod.ALL_WEEK,
        ).exists()
        assert TimePeriod.objects.filter(
            profile__name=profile_name,
            start="08:00",
            valid_during=TimePeriod.WEEKDAYS,
        ).exists()
        assert TimePeriod.objects.filter(
            profile__name=profile_name,
            start="16:00",
            valid_during=TimePeriod.WEEKDAYS,
        ).exists()
        assert TimePeriod.objects.filter(
            profile__name=profile_name,
            start="08:00",
            valid_during=TimePeriod.WEEKENDS,
        ).exists()

    def test_alertprofiles_save_profile_with_str_id_should_fail(self, db, client):
        url = reverse('alertprofiles-profile-save')
        profile_name = 'Catch 22'

        response = client.post(
            url,
            follow=True,
            data={
                'id': "-9337'))) ORDER BY 1-- SVmx",
                'name': profile_name,
                'daily_dispatch_time': '08:00',
                'weekly_dispatch_time': '08:00',
                'weekly_dispatch_day': AlertProfile.MONDAY,
            },
        )

        assert response.status_code == 404
        assert 'Requested profile does not exist' in smart_str(response.content)
        assert not AlertProfile.objects.filter(name=profile_name).exists()

    def test_alertprofiles_save_profile_with_non_existent_id_should_fail(
        self, db, client
    ):
        url = reverse('alertprofiles-profile-save')
        profile_name = 'Catch 22'
        last_alert_profile_id = getattr(AlertProfile.objects.last(), "pk", 0)

        response = client.post(
            url,
            follow=True,
            data={
                'id': last_alert_profile_id + 1,
                'name': profile_name,
                'daily_dispatch_time': '08:00',
                'weekly_dispatch_time': '08:00',
                'weekly_dispatch_day': AlertProfile.MONDAY,
            },
        )

        assert response.status_code == 404
        assert 'Requested profile does not exist' in smart_str(response.content)
        assert not AlertProfile.objects.filter(name=profile_name).exists()

    def test_alertprofiles_confirm_remove_profile(self, db, client, dummy_profile):
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'confirm': '1',
                'element': [dummy_profile.id],
            },
        )
        assert response.status_code == 200
        assert AlertProfile.objects.filter(pk=dummy_profile.pk).count() == 0

    def test_alertprofiles_remove_profile(self, db, client, activated_dummy_profile):
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'profile': [activated_dummy_profile.id],
            },
        )
        assert response.status_code == 200
        assert "Confirm deletion" in smart_str(response.content)
        assert activated_dummy_profile.name in smart_str(response.content)
        assert AlertProfile.objects.filter(pk=activated_dummy_profile.pk).count() == 1

    def test_alertprofiles_activate_profile(self, db, client, dummy_profile):
        # remarkably, activation/deactivation of profiles belong in the remove view!
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'activate': dummy_profile.id,
            },
        )
        assert response.status_code == 200
        assert "Active profile set" in smart_str(response.content)
        assert dummy_profile.name in smart_str(response.content)
        preference = AlertPreference.objects.get(account=dummy_profile.account)
        assert preference.active_profile == dummy_profile

    def test_alertprofiles_activate_profile_with_info_in_key(
        self, db, client, dummy_profile
    ):
        # remarkably, activation/deactivation of profiles belong in the remove view!
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                f'activate={dummy_profile.id}': ["Activate"],
            },
        )
        assert response.status_code == 200
        assert "Active profile set" in smart_str(response.content)
        assert dummy_profile.name in smart_str(response.content)
        preference = AlertPreference.objects.get(account=dummy_profile.account)
        assert preference.active_profile == dummy_profile

    def test_alertprofiles_deactivate_profile(
        self, db, client, activated_dummy_profile
    ):
        # remarkably, activation/deactivation of profiles belong in the remove view!
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'deactivate': activated_dummy_profile.id,
            },
        )
        assert response.status_code == 200
        print(type(response.content))
        assert "was deactivated" in smart_str(response.content)
        assert activated_dummy_profile.name in smart_str(response.content)
        preference = AlertPreference.objects.get(
            account=activated_dummy_profile.account
        )
        assert preference.active_profile is None

    def test_alertprofiles_deactivate_profile_with_info_in_key(
        self, db, client, activated_dummy_profile
    ):
        # remarkably, activation/deactivation of profiles belong in the remove view!
        url = reverse('alertprofiles-profile-remove')
        response = client.post(
            url,
            follow=True,
            data={
                f'deactivate={activated_dummy_profile.id}': ["Deactivate"],
            },
        )
        assert response.status_code == 200
        print(type(response.content))
        assert "was deactivated" in smart_str(response.content)
        assert activated_dummy_profile.name in smart_str(response.content)
        preference = AlertPreference.objects.get(
            account=activated_dummy_profile.account
        )
        assert preference.active_profile is None


class TestsFilters:
    def test_alertprofiles_add_private_filter_should_succeed(self, client):
        """Tests that an admin can POST a new private filter"""
        url = reverse("alertprofiles-filters-save")
        data = {
            "id": "",
            "name": "foobar",
            "owner": "admin",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200

    def test_alertprofiles_add_public_filter_should_succeed(self, client):
        """Tests that an admin can POST a new public filter"""
        url = reverse("alertprofiles-filters-save")
        data = {
            "id": "",
            "name": "foobar",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200


class TestsAddExpressions:
    class TestsIpAddresses:
        def test_valid_ipv4_address_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a valid IPv4 address can be added"""
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "172.0.0.1",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_valid_ipv6_address_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a valid IPv6 address can be added"""
            url = reverse("alertprofiles-filters-saveexpression")
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "2001:db8:3333:4444:5555:6666:7777:8888",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_valid_cidr_address_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a valid CIDR address can be added"""
            url = reverse("alertprofiles-filters-saveexpression")
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "129.241.190.0/24",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_non_valid_ip_address_should_fail(self, client, dummy_filter):
            """Tests that an expression with a not valid IP address cannot be added"""
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "wrong",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert not Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Invalid IP address: {data['value']}" in smart_str(response.content)

        def test_non_valid_cidr_address_should_fail(self, client, dummy_filter):
            """Tests that an expression with a not valid CIDR address cannot be added"""
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "10.0.2.1/28",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert not Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Invalid IP address: {data['value']}" in smart_str(response.content)

        def test_multiple_valid_ip_addresses_should_succeed(self, client, dummy_filter):
            """Tests that an expression with multiple valid IP addresses can be added"""
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.IN,
                "value": "172.0.0.1 2001:db8:3333:4444:5555:6666:7777:8888 "
                "129.241.190.0/24",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.IN,
                value=data["value"].replace(' ', '|'),
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_multiple_non_valid_ip_addresses_should_fail(
            self, client, dummy_filter
        ):
            """Tests that an expression with a not valid IP address cannot be added"""
            ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
            valid_ip = "172.0.0.1"
            invalid_ip = "wrong"
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": ip_match_field.pk,
                "operator": Operator.IN,
                "value": f"{valid_ip} {invalid_ip}",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert not Expression.objects.filter(
                filter=dummy_filter,
                match_field=ip_match_field,
                operator=Operator.IN,
                value=data["value"],
            ).exists()
            assert f"Invalid IP address: {invalid_ip}" in smart_str(response.content)

    class TestsSysname:
        def test_equal_sysname_should_succeed(self, client, dummy_filter):
            """Tests that an expression with an equals condition for sysname can be
            added
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.EQUALS,
                "value": "abc",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.EQUALS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_not_equal_sysname_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a not equal condition can be added for
            sysname
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.NOT_EQUAL,
                "value": "abc",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.NOT_EQUAL,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_starts_with_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a starts with condition can be added for
            sysname
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.STARTSWITH,
                "value": "a",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.STARTSWITH,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_ends_with_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a ends with condition can be added for
            sysname
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.ENDSWITH,
                "value": "a",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.ENDSWITH,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_contains_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a contains condition can be added for
            sysname
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.CONTAINS,
                "value": "a",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.CONTAINS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_regexp_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with a regexp condition can be added for
            sysname
            """
            group_match_field = MatchField.objects.get(name="Sysname")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.REGEXP,
                "value": "[^A-Z0-9]",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.REGEXP,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

    class TestsSeverity:
        def test_greater_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with greater severity can be added"""
            group_match_field = MatchField.objects.get(name="Severity")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.GREATER,
                "value": "3",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.GREATER,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_greater_equal_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with greater or equal severity can be added"""
            group_match_field = MatchField.objects.get(name="Severity")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.GREATER_EQ,
                "value": "3",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.GREATER_EQ,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_less_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with less severity can be added"""
            group_match_field = MatchField.objects.get(name="Severity")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.LESS,
                "value": "3",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.LESS,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_less_equal_condition_should_succeed(self, client, dummy_filter):
            """Tests that an expression with less or equal severity can be added"""
            group_match_field = MatchField.objects.get(name="Severity")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.LESS_EQ,
                "value": "3",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.LESS_EQ,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

        def test_not_equal_severity_should_succeed(self, client, dummy_filter):
            """Tests that an expression with not equal severity can be added"""
            group_match_field = MatchField.objects.get(name="Severity")
            url = reverse("alertprofiles-filters-saveexpression")
            data = {
                "filter": dummy_filter.pk,
                "match_field": group_match_field.pk,
                "operator": Operator.NOT_EQUAL,
                "value": "3",
            }
            response = client.post(url, data=data, follow=True)
            assert response.status_code == 200
            assert Expression.objects.filter(
                filter=dummy_filter,
                match_field=group_match_field,
                operator=Operator.NOT_EQUAL,
                value=data["value"],
            ).exists()
            assert f"Added expression to filter {dummy_filter}" in smart_str(
                response.content
            )

    def test_in_condition_should_succeed(self, client, dummy_filter):
        """Tests that an expression with an in condition can be added, alert type is
        just an example
        """
        string_match_field = MatchField.objects.get(name="Alert type")
        url = reverse("alertprofiles-filters-saveexpression")
        data = {
            "filter": dummy_filter.pk,
            "match_field": string_match_field.pk,
            "operator": Operator.IN,
            "value": ["apDown", "apUp"],
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert Expression.objects.filter(
            filter=dummy_filter,
            match_field=string_match_field,
            operator=Operator.IN,
            value="|".join(data["value"]),
        ).exists()
        assert f"Added expression to filter {dummy_filter}" in smart_str(
            response.content
        )

    def test_equal_condition_should_succeed(self, client, dummy_filter):
        """Tests that an expression with an equals condition can be added, group is
        just an example
        """
        group_match_field = MatchField.objects.get(name="Group")
        url = reverse("alertprofiles-filters-saveexpression")
        data = {
            "filter": dummy_filter.pk,
            "match_field": group_match_field.pk,
            "operator": Operator.EQUALS,
            "value": "AD",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert Expression.objects.filter(
            filter=dummy_filter,
            match_field=group_match_field,
            operator=Operator.EQUALS,
            value=data["value"],
        ).exists()
        assert f"Added expression to filter {dummy_filter}" in smart_str(
            response.content
        )


class TestsAddExpressionsHelpModal:
    def test_should_render_add_expression_help_modal(self, client):
        url = reverse('alertprofiles-filters-addexpression-operator-help')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="operator-help"' in smart_str(response.content)


class TestsPermissions:
    def test_set_accountgroup_permissions_should_not_crash(self, db, client):
        """Regression test for #2281"""
        url = reverse('alertprofiles-permissions-save')
        response = client.post(
            url,
            follow=True,
            data={
                'filter_group': '71',  # G01 All alerts, as hardcoded in navprofiles.sql
                'group': '3',  # Authenticated users
            },
        )
        assert response.status_code == 200

    def test_should_include_permissions_help_trigger(self, client):
        url = reverse('alertprofiles-permissions')
        modal_url = reverse('alertprofiles-permissions-help')
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}"' in smart_str(response.content)

    def test_should_render_permissions_help_modal(self, client):
        url = reverse('alertprofiles-permissions-help')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="permissions-help"' in smart_str(response.content)


class TestsAlertAddresses:
    def test_alertprofiles_add_slack_address_with_valid_url_should_succeed(
        self, client
    ):
        """Tests that a slack address with a valid absolute url can be added"""
        valid_url = "https://example.com"
        slack = AlertSender.objects.get(name=AlertSender.SLACK)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_url,
            "type": slack.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=slack,
            address=valid_url,
        ).exists()
        assert f"Saved address {valid_url}" in smart_str(response.content)

    def test_alertprofiles_add_slack_address_with_a_valid_but_not_absolute_url_should_fail(  # noqa: E501
        self,
        client,
    ):
        """Tests that a slack address with a not valid url cannot be added"""
        non_absolute_url = "www.example.com"
        slack = AlertSender.objects.get(name=AlertSender.SLACK)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": non_absolute_url,
            "type": slack.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert not AlertAddress.objects.filter(
            type=slack,
            address=non_absolute_url,
        ).exists()
        assert "Not a valid absolute url." in smart_str(response.content)

    def test_alertprofiles_add_slack_address_with_non_valid_url_should_fail(
        self, client
    ):
        """Tests that a slack address with a not valid url cannot be added"""
        invalid_url = "abc"
        slack = AlertSender.objects.get(name=AlertSender.SLACK)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": invalid_url,
            "type": slack.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert not AlertAddress.objects.filter(
            type=slack,
            address=invalid_url,
        ).exists()
        assert "Not a valid absolute url." in smart_str(response.content)

    def test_alertprofiles_add_valid_email_address_should_succeed(self, client):
        """Tests that a valid email address can be added"""
        valid_email_address = "hello@example.com"
        email = AlertSender.objects.get(name=AlertSender.EMAIL)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_email_address,
            "type": email.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=email,
            address=valid_email_address,
        ).exists()
        assert f"Saved address {valid_email_address}" in smart_str(response.content)

    def test_alertprofiles_add_invalid_email_address_should_fail(self, client):
        """Tests that an invalid email address cannot be added"""
        invalid_email_address = "abc"
        email = AlertSender.objects.get(name=AlertSender.EMAIL)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": invalid_email_address,
            "type": email.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert not AlertAddress.objects.filter(
            type=email,
            address=invalid_email_address,
        ).exists()
        assert "Not a valid email address." in smart_str(response.content)

    def test_alertprofiles_add_valid_phone_number_without_country_code_should_succeed(
        self,
        client,
    ):
        """Tests that a valid phone number without a country code can be added"""
        valid_phone_number = "47474747"
        sms = AlertSender.objects.get(name=AlertSender.SMS)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_phone_number,
            "type": sms.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=sms,
            address=valid_phone_number,
        ).exists()
        assert f"Saved address {valid_phone_number}" in smart_str(response.content)

    def test_alertprofiles_add_valid_non_norwegian_phone_number_without_country_code_should_succeed(  # noqa: E501
        self,
        client,
    ):
        """Tests that a valid phone number without a country code can be added"""
        valid_phone_number = "02227661193"
        sms = AlertSender.objects.get(name=AlertSender.SMS)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_phone_number,
            "type": sms.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=sms,
            address=valid_phone_number,
        ).exists()
        assert f"Saved address {valid_phone_number}" in smart_str(response.content)

    def test_alertprofiles_add_valid_phone_number_with_country_code_should_succeed(
        self, client
    ):
        """Tests that a valid phone number with a country code (+xx) can be added"""
        valid_phone_number = "+4747474747"
        sms = AlertSender.objects.get(name=AlertSender.SMS)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_phone_number,
            "type": sms.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=sms,
            address=valid_phone_number,
        ).exists()
        assert f"Saved address {valid_phone_number}" in smart_str(response.content)

    def test_alertprofiles_add_valid_phone_number_with_double_zero_country_code_should_succeed(  # noqa: E501
        self,
        client,
    ):
        """
        Tests that a valid phone number with a country code with double zero (00xx) can
        be added"""
        valid_phone_number = "004747474747"
        sms = AlertSender.objects.get(name=AlertSender.SMS)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": valid_phone_number,
            "type": sms.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert AlertAddress.objects.filter(
            type=sms,
            address=valid_phone_number,
        ).exists()
        assert f"Saved address {valid_phone_number}" in smart_str(response.content)

    def test_alertprofiles_add_invalid_phone_number_should_fail(self, client):
        """Tests that an invalid phone number cannot be added"""
        invalid_phone_number = "abc"
        sms = AlertSender.objects.get(name=AlertSender.SMS)
        url = reverse("alertprofiles-address-save")
        data = {
            "address": invalid_phone_number,
            "type": sms.pk,
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert not AlertAddress.objects.filter(
            type=sms,
            address=invalid_phone_number,
        ).exists()
        assert "Not a valid phone number." in smart_str(response.content)


class TestsFilterGroups:
    def test_alertprofiles_confirm_remove_filter_group(
        self, db, client, dummy_filter_group
    ):
        url = reverse('alertprofiles-filter_groups-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'confirm': '1',
                'element': [dummy_filter_group.id],
            },
        )
        assert response.status_code == 200
        assert not FilterGroup.objects.filter(pk=dummy_filter_group.pk).exists()

    def test_alertprofiles_remove_filter_group(self, db, client, dummy_filter_group):
        url = reverse('alertprofiles-filter_groups-remove')
        response = client.post(
            url,
            follow=True,
            data={
                'filter_group': [dummy_filter_group.id],
            },
        )
        assert response.status_code == 200
        assert "Confirm deletion" in smart_str(response.content)
        assert dummy_filter_group.name in smart_str(response.content)
        assert FilterGroup.objects.filter(pk=dummy_filter_group.pk).count() == 1

    def test_alertprofiles_move_filter_within_group_should_not_crash(
        self, db, client, dummy_filter_group
    ):
        """Regression test for #2979: Ensuring that pre-processing of request data
        doesn't crash unexpectedly.
        """
        url = reverse('alertprofiles-filter_groups-removefilter')
        response = client.post(
            url,
            follow=True,
            data={
                "moveup=23": "Move+up",
                "id": dummy_filter_group.id,
            },
        )
        assert response.status_code in (200, 404)

    def test_should_include_operator_help_trigger(self, client, dummy_filter_group):
        url = reverse(
            'alertprofiles-filter_groups-detail', args=[dummy_filter_group.pk]
        )
        modal_url = reverse('alertprofiles-filter_groups-operator-help')
        response = client.get(url)
        assert response.status_code == 200
        assert f'hx-get="{modal_url}"' in smart_str(response.content)

    def test_should_render_operator_help_modal(self, client):
        url = reverse('alertprofiles-filter_groups-operator-help')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="operator-help"' in smart_str(response.content)


#
# fixtures and helpers
#


@pytest.fixture(scope='function')
def dummy_profile(admin_account):
    account = admin_account
    profile = AlertProfile(account=account, name='ÆØÅ Profile %d' % randint(1, 1000))
    profile.save()
    return profile


@pytest.fixture(scope='function')
def activated_dummy_profile(dummy_profile):
    preference = AlertPreference(
        account=dummy_profile.account, active_profile=dummy_profile
    )
    preference.save()
    return dummy_profile


@pytest.fixture(scope="function")
def dummy_time_period(activated_dummy_profile):
    time_period = TimePeriod(profile=activated_dummy_profile)
    time_period.save()
    return time_period


@pytest.fixture(scope="function")
def dummy_alert_address(admin_account):
    alert_address = AlertAddress(
        account=admin_account,
        type=AlertSender.objects.get(name=AlertSender.SMS),
        address="admin@example.com",
    )
    alert_address.save()
    return alert_address


@pytest.fixture(scope="function")
def dummy_alert_subscription(
    dummy_alert_address, dummy_time_period, dummy_filter_group
):
    alert_subscription = AlertSubscription(
        alert_address=dummy_alert_address,
        time_period=dummy_time_period,
        filter_group=dummy_filter_group,
    )
    alert_subscription.save()
    return alert_subscription


@pytest.fixture(scope="function")
def dummy_filter(admin_account):
    filtr = Filter(name="dummy", owner=admin_account)
    filtr.save()
    return filtr


@pytest.fixture(scope="function")
def dummy_filter_group(admin_account):
    filter_group = FilterGroup(name="dummy_group", owner=admin_account)
    filter_group.save()
    return filter_group

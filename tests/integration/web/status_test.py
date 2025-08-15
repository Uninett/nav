# -*- coding: utf-8 -*-

import base64
import pickle

from django.urls import reverse
from django.utils.encoding import smart_str


#########
# Tests #
#########


def test_set_and_get_default_status_filter_should_show_filter(client):
    url = reverse('status2_save_preferences')
    response = client.post(
        url,
        follow=True,
        data={
            "status_filters": "alert_type",
            "alert_type": "linkDegraded",
            "stateless_threshold": "24",
        },
    )
    assert response.status_code == 200

    url = reverse('status2-index')
    response = client.get(url)
    assert response.status_code == 200
    assert '<option value="linkDegraded" selected>linkDegraded</option>' in smart_str(
        response.content
    )


def test_get_default_status_filter_should_show_filter_for_encoded_filter(
    client, admin_account
):
    datastring = base64.b64encode(
        pickle.dumps(
            {
                "status_filters": "alert_type",
                "alert_type": "linkDegraded",
                "stateless_threshold": "24",
            }
        )
    )
    admin_account.preferences[admin_account.PREFERENCE_KEY_STATUS] = datastring
    admin_account.save()

    url = reverse('status2-index')
    response = client.get(url)
    assert response.status_code == 200
    assert '<option value="linkDegraded" selected>linkDegraded</option>' in smart_str(
        response.content
    )

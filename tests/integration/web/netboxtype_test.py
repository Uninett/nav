# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from nav.models.manage import NetboxType
from nav.web.seeddb.forms import SEPARATOR

from django.urls import reverse
from django.utils.encoding import smart_str


def test_post_netboxtype_with_sysobjectid_without_leading_period_should_succeed(client):
    vendor = "hp"
    name = "A5120-48P-EI"
    sysobjectid = "1.3.6.1.4.1.25506.1.516"
    description = "HP Procurve A5120"
    url = reverse('seeddb-type-edit')

    response = client.post(
        url,
        follow=True,
        data={
            "vendor": vendor,
            "name": name,
            "sysobjectid": sysobjectid,
            "description": description,
            "submit": "Save+netbox+type",
        },
    )

    assert response.status_code == 200
    assert f"Saved netbox type {name} ({description} from {vendor})" in smart_str(
        response.content
    )
    assert NetboxType.objects.filter(sysobjectid=sysobjectid.strip(SEPARATOR)).exists()


def test_post_netboxtype_with_sysobjectid_with_leading_period_should_succeed(client):
    vendor = "hp"
    name = "A5120-48P-EI-2"
    sysobjectid = ".1.3.6.1.4.1.25506.1.517"
    description = "HP Procurve A5120 V2"
    url = reverse('seeddb-type-edit')

    response = client.post(
        url,
        follow=True,
        data={
            "vendor": vendor,
            "name": name,
            "sysobjectid": sysobjectid,
            "description": description,
            "submit": "Save+netbox+type",
        },
    )

    assert response.status_code == 200
    assert f"Saved netbox type {name} ({description} from {vendor})" in smart_str(
        response.content
    )
    assert NetboxType.objects.filter(sysobjectid=sysobjectid.strip(SEPARATOR)).exists()


def test_post_netboxtype_with_sysobjectid_being_invalid_should_fail(client):
    vendor = "hp"
    name = "A5120-48P-EI-3"
    sysobjectid = "not just periods and numbers"
    description = "HP Procurve A5120 V3"
    url = reverse('seeddb-type-edit')

    response = client.post(
        url,
        follow=True,
        data={
            "vendor": vendor,
            "name": name,
            "sysobjectid": sysobjectid,
            "description": description,
            "submit": "Save+netbox+type",
        },
    )

    assert response.status_code == 200
    assert "Sysobjectid can only contain digits and periods." in smart_str(
        response.content
    )
    assert not NetboxType.objects.filter(sysobjectid=sysobjectid).exists()

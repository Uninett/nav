"""Tests nav/bin/update_ouis.py script for updating OUI records"""

from unittest.mock import Mock
import pytest

from nav.models.oui import OUI
from nav.bin.update_ouis import run as update_ouis


def test_vendor_name_should_be_registered_correctly(db, mock_oui_file):
    update_ouis()
    ingram = OUI.objects.get(oui="10-E9-92-00-00-00")
    assert ingram.vendor == "INGRAM MICRO SERVICES"


def test_oui_should_be_registered_as_mac_address_with_last_3_octets_as_zeros(
    db, mock_oui_file
):
    update_ouis()
    assert OUI.objects.filter(oui="10-E9-92-00-00-00").exists()


def test_all_unique_ouis_should_be_registered(db, mock_oui_file):
    update_ouis()
    assert OUI.objects.count() == 5


def test_duplicate_ouis_should_not_be_registered(db, mock_duplicate_oui_file):
    """
    The OUI file we use is known to have duplicate OUIs, but only one should be
    registered
    """
    update_ouis()
    assert OUI.objects.count() == 1


def test_old_ouis_should_be_deleted_if_they_dont_exist_in_new_oui_file(
    db, mock_oui_file
):
    old_vendor_oui = "AA-AA-AA-00-00-00"
    OUI.objects.create(oui=old_vendor_oui, vendor="Old vendor")
    update_ouis()
    assert OUI.objects.count() == 5
    assert not OUI.objects.filter(oui=old_vendor_oui).exists()


def test_invalid_oui_should_not_be_registered(db, mock_invalid_oui_file):
    update_ouis()
    assert OUI.objects.count() == 0


@pytest.fixture()
def mock_oui_file(monkeypatch):
    mocked_oui_data = """
OUI/MA-L                                                    Organization
company_id                                                  Organization
                                                            Address

10-E9-92   (hex)		    INGRAM MICRO SERVICES
10E992     (base 16)		INGRAM MICRO SERVICES
                            100 CHEMIN DE BAILLOT
                            MONTAUBAN    82000
                            FR

78-F2-76   (hex)		    Cyklop Fastjet Technologies (Shanghai) Inc.
78F276     (base 16)		Cyklop Fastjet Technologies (Shanghai) Inc.
                            No 18?Lane 699, Zhang Wengmiao Rd,  Fengxian district, Shanghai China
                            Shanghai    201401
                            CN

28-6F-B9   (hex)		    Nokia Shanghai Bell Co., Ltd.
286FB9     (base 16)		Nokia Shanghai Bell Co., Ltd.
                            No.388 Ning Qiao Road,Jin Qiao Pudong Shanghai
                            Shanghai     201206
                            CN

E0-A1-29   (hex)		    Extreme Networks Headquarters
E0A129     (base 16)		Extreme Networks Headquarters
                            2121 RDU Center Drive
                            Morrisville  NC  27560
                            US

A8-C6-47   (hex)		    Extreme Networks Headquarters
A8C647     (base 16)		Extreme Networks Headquarters
                            2121 RDU Center Drive
                            Morrisville  NC  27560
                            US
    """  # noqa: E501
    download_file_mock = Mock(return_value=mocked_oui_data)
    monkeypatch.setattr("nav.bin.update_ouis._download_oui_file", download_file_mock)


@pytest.fixture()
def mock_duplicate_oui_file(monkeypatch):
    mocked_oui_data = """
OUI/MA-L                                                    Organization
company_id                                                  Organization
                                                            Address

08-00-30   (hex)		    NETWORK RESEARCH CORPORATION
080030     (base 16)		NETWORK RESEARCH CORPORATION
                            2380 N. ROSE AVENUE
                            OXNARD  CA  93010
                            US

08-00-30   (hex)		    ROYAL MELBOURNE INST OF TECH
080030     (base 16)		ROYAL MELBOURNE INST OF TECH
                            GPO BOX 2476V
                            MELBOURNE  VIC  3001
                            AU

08-00-30   (hex)		    CERN
080030     (base 16)		CERN
                            CH-1211
                            GENEVE  SUISSE/SWITZ  023
                            CH
    """
    download_file_mock = Mock(return_value=mocked_oui_data)
    monkeypatch.setattr("nav.bin.update_ouis._download_oui_file", download_file_mock)


@pytest.fixture()
def mock_invalid_oui_file(monkeypatch):
    mocked_oui_data = """
OUI/MA-L                                                    Organization
company_id                                                  Organization
                                                            Address

invalidhex   (hex)		    INGRAM MICRO SERVICES
10E992     (base 16)		INGRAM MICRO SERVICES
                            100 CHEMIN DE BAILLOT
                            MONTAUBAN    82000
                            FR
    """
    download_file_mock = Mock(return_value=mocked_oui_data)
    monkeypatch.setattr("nav.bin.update_ouis._download_oui_file", download_file_mock)

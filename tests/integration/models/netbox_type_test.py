from nav.enterprise.ids import VENDOR_ID_H3C
from nav.models.manage import NetboxType


class TestNetboxType(object):
    def test_get_enterprise_id_returns_correctly_for_sysobjectid_with_leading_period(
        self,
    ):
        sysobjectid = ".1.3.6.1.4.1.25506.1.517"
        netbox_type = NetboxType(
            vendor_id="hp",
            name="A5120-48P-EI-2",
            description="HP Procurve A5120 V2",
            sysobjectid=sysobjectid,
        )

        assert netbox_type.get_enterprise_id() == VENDOR_ID_H3C

    def test_get_enterprise_id_returns_correctly_for_sysobjectid_without_leading_period(
        self,
    ):
        sysobjectid = "1.3.6.1.4.1.25506.1.517"
        netbox_type = NetboxType(
            vendor_id="hp",
            name="A5120-48P-EI-2",
            description="HP Procurve A5120 V2",
            sysobjectid=sysobjectid,
        )

        assert netbox_type.get_enterprise_id() == VENDOR_ID_H3C

    def test_get_enterprise_id_returns_none_for_sysobjectid_of_wrong_format(
        self,
    ):
        sysobjectid = "abc"
        netbox_type = NetboxType(
            vendor_id="hp",
            name="A5120-48P-EI-2",
            description="HP Procurve A5120 V2",
            sysobjectid=sysobjectid,
        )

        assert netbox_type.get_enterprise_id() is None

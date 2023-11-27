from nav.web.seeddb.page.management_profile.forms import SnmpV3Form


class TestSnmpv3Form:
    def test_when_seclevel_is_noauth_then_it_should_not_require_auth_password(self):
        form = SnmpV3Form(
            dict(
                sec_level="noAuthNoPriv",
                auth_protocol="MD5",
                sec_name="foo",
                auth_password="",
            )
        )
        assert form.is_valid()

    def test_when_seclevel_is_auth_then_it_should_require_auth_password(self):
        form = SnmpV3Form(
            dict(
                sec_level="authNoPriv",
                auth_protocol="MD5",
                sec_name="foo",
                auth_password="",
            )
        )
        assert not form.is_valid()

    def test_when_seclevel_is_priv_then_it_should_require_priv_password(self):
        form = SnmpV3Form(
            dict(
                sec_level="authPriv",
                auth_protocol="MD5",
                sec_name="foo",
                auth_password="bar",
            )
        )
        assert not form.is_valid()

    def test_when_seclevel_is_priv_then_it_should_accept_priv_password(self):
        form = SnmpV3Form(
            dict(
                sec_level="authPriv",
                auth_protocol="MD5",
                sec_name="foo",
                auth_password="bar",
                priv_password="cromulent",
            )
        )
        assert form.is_valid()

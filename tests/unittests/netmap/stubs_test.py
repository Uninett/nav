from nav.netmap.stubs import Netbox
from nav.models import manage


class TestNetboxEqWithNonStubValues:
    def test_when_value_is_orm_model_with_same_sysname_it_should_return_true(self):
        localhost = manage.Netbox(sysname='localhost')
        stub = Netbox()
        stub.sysname = localhost.sysname
        assert stub == localhost

    def test_when_value_is_orm_model_with_different_sysname_it_should_return_false(
        self,
    ):
        localhost = manage.Netbox(sysname='localhost')
        stub = Netbox()
        stub.sysname = "stubhost"
        assert stub != localhost

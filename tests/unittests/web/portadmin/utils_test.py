from unittest.mock import patch, Mock

from nav.web.portadmin.utils import set_editable_flag_on_interfaces


class TestSetEditableFlagOnInterfaces:
    def test_when_user_is_admin_it_should_set_all_interfaces_to_editable(self):
        with patch(
            "nav.web.portadmin.utils.should_check_access_rights", return_value=False
        ):
            mock_admin = Mock()
            mock_interfaces = [Mock(iseditable=False)] * 3
            set_editable_flag_on_interfaces(mock_interfaces, [], mock_admin)

            assert all(ifc.iseditable for ifc in mock_interfaces)

    def test_when_user_is_not_admin_it_should_set_only_matching_interfaces_to_editable(
        self,
    ):
        with patch(
            "nav.web.portadmin.utils.should_check_access_rights", return_value=True
        ):
            mock_user = Mock()
            mock_vlans = [Mock(vlan=42), Mock(vlan=69), Mock(vlan=666)]
            editable_interface = Mock(vlan=666, iseditable=False)
            mock_interfaces = [
                Mock(vlan=99, iseditable=False),
                editable_interface,
                Mock(vlan=27, iseditable=False),
            ]

            set_editable_flag_on_interfaces(mock_interfaces, mock_vlans, mock_user)

            assert editable_interface.iseditable
            assert all(
                not ifc.iseditable
                for ifc in mock_interfaces
                if ifc is not editable_interface
            )

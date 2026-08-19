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

    def test_when_user_may_not_edit_anything_no_interface_should_be_editable(self):
        permissions = Mock(can_edit_something=False)
        interfaces = [Mock(vlan=1, iseditable=True) for _ in range(3)]

        with patch(
            "nav.web.portadmin.utils.should_check_access_rights", return_value=False
        ):
            set_editable_flag_on_interfaces(
                interfaces, [Mock(vlan=1)], Mock(), permissions=permissions
            )

        assert not any(ifc.iseditable for ifc in interfaces)

    def test_when_user_may_edit_something_it_should_still_apply_the_vlan_rules(self):
        permissions = Mock(can_edit_something=True)
        editable = Mock(vlan=666, iseditable=False, to_netbox=None)
        interfaces = [Mock(vlan=99, iseditable=False, to_netbox=None), editable]

        with patch(
            "nav.web.portadmin.utils.should_check_access_rights", return_value=True
        ):
            set_editable_flag_on_interfaces(
                interfaces, [Mock(vlan=666)], Mock(), permissions=permissions
            )

        assert editable.iseditable
        assert not interfaces[0].iseditable

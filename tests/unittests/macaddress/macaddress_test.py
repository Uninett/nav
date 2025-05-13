#
# Copyright (C) 2012 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import pytest

from nav.macaddress import MacAddress, MacPrefix


def test_mac_address_too_short():
    with pytest.raises(ValueError):
        MacAddress("e4:2f")


def test_mac_address_too_long():
    with pytest.raises(ValueError):
        MacAddress("e4:2f:45:72:6e:76:01")


def test_mac_address_wrong_parameter_type_list():
    with pytest.raises(ValueError):
        MacAddress([])


def test_mac_address_wrong_parameter_type_dict():
    with pytest.raises(ValueError):
        MacAddress({})


def test_mac_address_address_contains_illegal_value():
    with pytest.raises(ValueError):
        MacAddress("e4:2f:45:72:6e:o6")


def test_mac_address_should_return_same_address_value_with_colon():
    param = 'e42f45726e76'
    mac_addr = MacAddress(param)
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_mac_addres_as_parameter_should_return_same_address():
    param = 'e42f45726e76'
    ma = MacAddress(param)
    mac_addr = MacAddress(ma)
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_return_same_address_value_with_colon():
    param = 'e4:2f:45:72:6e:76'
    mac_addr = MacAddress(param)
    assert str(mac_addr) == param


def test_mac_address_return_same_address_value_without_dash():
    param = 'e4-2f-45-72-6e-76'
    mac_addr = MacAddress(param)
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_return_same_address_value_without_spaces():
    param = 'e4 2f 45 72 6e 76'
    mac_addr = MacAddress(param)
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_return_same_address_value_without_dot():
    param = 'e42f.4572.6e76'
    mac_addr = MacAddress(param)
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_return_same_address_value_when_byte_string():
    param = b'\xe4\x2f\x45\x72\x6e\x76'
    mac_addr = MacAddress(MacAddress.from_octets(param))
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_with_byte_string_prefix_should_return_same_address():
    param = b'\xe4\x2f\x45\x72\x6e\x76'
    mac_addr = MacAddress(MacAddress.from_octets(param))
    assert str(mac_addr) == 'e4:2f:45:72:6e:76'


def test_mac_address_to_string_without_delimiter_return_same_address():
    param = 'e42f.4572.6e76'
    mac_addr = MacAddress(param)
    assert mac_addr.to_string() == 'e42f45726e76'


def test_mac_address_to_string_with_colon_delimiter_return_same_address():
    param = 'e4-2f-45-72-6e76'
    mac_addr = MacAddress(param)
    assert mac_addr.to_string(':') == 'e4:2f:45:72:6e:76'


def test_mac_address_to_string_with_dash_delimiter_return_same_address():
    param = 'e42f.4572.6e76'
    mac_addr = MacAddress(param)
    assert mac_addr.to_string('-') == 'e4-2f-45-72-6e-76'


def test_mac_address_to_string_with_dot_delimiter_return_same_address():
    param = 'e4:2f:45:72:6e:76'
    mac_addr = MacAddress(param)
    assert mac_addr.to_string('.') == 'e42f.4572.6e76'


def test_mac_address_param_as_int_should_return_same_in_hex():
    param = 11111110000
    mac_addr = MacAddress(param)
    assert str(mac_addr) == '00:02:96:46:15:70'


def test_mac_addresses_are_equal():
    mac_addr1 = MacAddress('01:23:45:67:89:ab')
    mac_addr2 = MacAddress('01:23:45:67:89:ab')
    assert mac_addr1 == mac_addr2


def test_mac_addresses_hash_the_same():
    mac_addr1 = MacAddress('01:23:45:67:89:ab')
    mac_addr2 = MacAddress('01:23:45:67:89:ab')
    assert hash(mac_addr1) == hash(mac_addr2)


def test_mac_addresses_hash_not_the_same():
    mac_addr1 = MacAddress('01:23:45:67:89:ab')
    mac_addr2 = MacAddress('01:23:45:67:89:ac')
    assert hash(mac_addr1) != hash(mac_addr2)


def test_mac_addresses_are_comparable():
    mac_addr1 = MacAddress('01:23:45:67:89:ab')
    mac_addr2 = MacAddress('01:23:45:67:89:cc')
    assert mac_addr1 < mac_addr2
    assert mac_addr2 > mac_addr1
    assert mac_addr1 <= mac_addr2
    assert mac_addr2 >= mac_addr1
    assert mac_addr1 != mac_addr2


def test_mac_address_should_compare_with_int():
    mac = MacAddress('01:23:45:67:89:ab')
    assert mac != 5


def test_mac_address_should_compare_with_string():
    mac = MacAddress('01:23:45:67:89:ab')
    assert mac == '01:23:45:67:89:ab'
    assert mac != 'blah'


def test_mac_address_with_byte_string_prefix_should_return_zero_padded_addr():
    param = b'\xe4\x2f\x45\x72'
    mac_addr = MacAddress.from_octets(param)
    assert str(mac_addr) == '00:00:e4:2f:45:72'


def test_macprefix_with_colon_prefix_should_return_same_prefix():
    param = 'e4:2f:45:f'
    mac_addr = MacPrefix(param)
    assert str(mac_addr) == 'e4:2f:45:f'


def test_macprefix_with_dash_prefix_should_return_same_prefix():
    param = 'e4-2f-45-f'
    mac_addr = MacPrefix(param)
    assert str(mac_addr) == 'e4:2f:45:f'


def test_macprefix_with_dot_prefix_should_return_same_prefix():
    param = 'e42f.45f'
    mac_addr = MacPrefix(param)
    assert str(mac_addr) == 'e4:2f:45:f'


def test_macprefix_should_return_zero_padded_when_address_start_with_zero():
    param = '01:01:01'
    mac_addr = MacPrefix(param)
    assert str(mac_addr) == '01:01:01'


def test_macprefix_should_return_zero_padded_when_address_start_with_5_zeros():
    param = '00:00:01'
    mac_addr = MacPrefix(param)
    assert str(mac_addr) == '00:00:01'


def test_macprefix_has_correct_length_with_prefix_length_six():
    param = 'e4:2f:45'
    mac_addr = MacPrefix(param)
    assert len(mac_addr) == 16777216


def test_macprefix_has_correct_length_with_prefix_length_seven():
    param = 'e4-2f-45-3'
    mac_addr = MacPrefix(param)
    assert len(mac_addr) == 1048576


def test_macprefix_has_correct_length_with_prefix_length_eigth():
    param = 'e42f.453d'
    mac_addr = MacPrefix(param)
    assert len(mac_addr) == 65536


def test_macprefix_has_correct_length_with_full_length_address():
    param = 'e4:2f:45:72:6e:76'
    mac_addr = MacPrefix(param)
    assert len(mac_addr) == 1


def test_macprefix_should_return_correct_value_with_zero_key():
    param = 'e42f.45'
    mac_addr = MacPrefix(param)
    assert str(mac_addr[0]) == 'e4:2f:45:00:00:00'


def test_macprefix_should_return_correct_value_with_key_equal_256():
    param = 'e4:2f:45:3d'
    mac_addr = MacPrefix(param)
    assert str(mac_addr[157]) == 'e4:2f:45:3d:00:9d'


def test_macprefix_should_return_correct_value_with_last_key():
    param = 'e4-2f-45'
    mac_addr = MacPrefix(param)
    assert str(mac_addr[-1]) == 'e4:2f:45:ff:ff:ff'

"""Tests for should_detain"""

import pytest

from mock import Mock, patch
from nav.arnold import (InExceptionListError, WrongCatidError,
                        BlockonTrunkError, raise_if_detainment_not_allowed,
                        check_non_block)


@patch('nav.arnold.get_config')
def test_should_detain_inexceptionlist(mock_getconfig):
    """Test that InExceptionListError is properly thrown"""
    with patch('nav.arnold.parse_nonblock_file') as parse:
        parse.return_value = {'ip': {'10.0.0.1': 1}}
        with pytest.raises(InExceptionListError):
            check_non_block('10.0.0.1')


@patch('nav.arnold.get_config')
def test_should_detain_wrongcatid(mock_getconfig, interface):
    """Test that WrongCatidError is properly thrown"""
    get_config = mock_getconfig.return_value
    get_config.get.return_value = 'SW,EDGE'

    category = interface.netbox.category
    category.id = 'GW'

    with pytest.raises(WrongCatidError):
        raise_if_detainment_not_allowed(interface)


@patch('nav.arnold.get_config')
def test_should_detain_blockontrunk(mock_getconfig, interface):
    """Test that BlockonTrunkError is properly thrown"""
    get_config = mock_getconfig.return_value
    get_config.get.return_value = 'SW,EDGE'

    interface.trunk = True

    with pytest.raises(BlockonTrunkError):
        raise_if_detainment_not_allowed(interface)


@pytest.fixture
def interface():
    """Mock interface model instance for testing"""
    category = Mock()
    category.id = 'SW'

    netbox = Mock()
    netbox.category = category

    interface = Mock()
    interface.netbox = netbox
    interface.trunk = True

    return interface

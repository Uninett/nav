"""Tests for should_detain"""
import unittest
from mock import Mock, patch
from nav.arnold import (InExceptionListError, WrongCatidError,
                        BlockonTrunkError, raise_if_detainment_not_allowed, check_non_block)

@patch('nav.arnold.get_config')
class TestArnoldShouldDetain(unittest.TestCase):
    """Tests for should_detain"""

    def setUp(self):
        self.interface = create_interface()

    def test_should_detain_inexceptionlist(self, mock_getconfig):
        """Test that InExceptionListError is properly thrown"""
        with patch('nav.arnold.parse_nonblock_file') as parse:
            parse.return_value = {'ip': {'10.0.0.1': 1}}
            arguments = ['10.0.0.1']
            self.assertRaises(InExceptionListError, check_non_block, *arguments)


    def test_should_detain_wrongcatid(self, mock_getconfig):
        """Test that WrongCatidError is properly thrown"""
        get_config = mock_getconfig.return_value
        get_config.get.return_value = 'SW,EDGE'

        interface = self.interface
        category = interface.netbox.category
        category.id = 'GW'

        arguments = [interface]
        self.assertRaises(WrongCatidError, raise_if_detainment_not_allowed, *arguments)

    def test_should_detain_blockontrunk(self, mock_getconfig):
        """Test that BlockonTrunkError is properly thrown"""
        get_config = mock_getconfig.return_value
        get_config.get.return_value = 'SW,EDGE'

        interface = self.interface
        interface.trunk = True
        arguments = [interface]

        self.assertRaises(BlockonTrunkError, raise_if_detainment_not_allowed, *arguments)


def create_interface():
    """Mock interface model instance for testing"""
    category = Mock()
    category.id = 'SW'

    netbox = Mock()
    netbox.category = category

    interface = Mock()
    interface.netbox = netbox
    interface.trunk = True

    return interface


import pytest
from nav.mibs.lldp_mib import LLDPMib


def test_broken_remote_table_result_should_be_detected(
    table_with_too_short_index, table_with_too_long_index
):
    assert LLDPMib._is_remote_table_index_broken(table_with_too_short_index)
    assert LLDPMib._is_remote_table_index_broken(table_with_too_long_index)


def test_ok_remote_table_result_should_be_detected(ok_remote_table):
    assert not LLDPMib._is_remote_table_index_broken(ok_remote_table)


#
# Fixtures go here
#


@pytest.fixture
def table_with_too_short_index():
    return {index: {0: index} for index in ((1000,), (1002,))}


@pytest.fixture
def table_with_too_long_index():
    return {index: {0: index} for index in ((0, 1000, 2, 3), (0, 1002, 2, 3))}


@pytest.fixture
def ok_remote_table():
    return {index: {0: index} for index in ((0, 1000, 2), (0, 1002, 2))}

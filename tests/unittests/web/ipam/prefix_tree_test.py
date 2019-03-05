import pytest
from nav.web.ipam.prefix_tree import make_tree_from_ip

# TODO: Mock prefixes via fixtures?


def test_prefix_tree_invalid_cidr():
    cidrs = ["192.168.1.1/42"]
    with pytest.raises(ValueError):
        make_tree_from_ip(cidrs)


def test_prefix_tree_valid_cidr():
    cidrs = ["10.0.0.0/16", "10.0.1.0/24"]
    tree = make_tree_from_ip(cidrs)
    # sanity check: tree root should have children
    assert tree.children_count > 0
    # sanity check: spanned prefix should be within spanning prefix
    child = tree.children[0].children[0]
    assert child.prefix == "10.0.1.0/24"
    assert child.prefixlen == 24

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Builds and represents IP nets in a tree structure."""

from copy import deepcopy
from nav import db
from nav.ip import IP
from nav.report.IPtools import getMask, sort_nets_by_prefixlength, andIpMask


def build_tree(start_net, end_net=None, bits_in_matrix=0,
               add_missing_nets=False):
    """Builds a tree from start_net to (and included) end_net.

    Arguments:
        start_net: IPy.IP instance of the starting point

    Returns: A tree (using a hash map)

    This module was originally implemented for the prefix matrix which
    needed three additional options:
        end_net: The last net to be shown in the matrix
        bits_in_matrix: Number of bits to exclude from the end_net IP,
            defaults to 0
        add_missing_nets: If a leaf nodes' parent does not have prefix
            length == (end_net - bits_in_matrix) such a parent will be added
            in between the leaf and the original parent. The extra parent
            will serve as a 'foreign key' later on when the prefix matrix
            splits the tree on all nodes with prefix length =
            end_net.prefixlen() - bits_in_matrix.

            defaults to False
    """

    result = {start_net: {}}
    subnets = get_subnets(start_net)
    sorted_subnets = sort_nets_by_prefixlength(subnets)

    # TODO: Reimplement this to respect that the list is allready sorted,
    #       that way we won't have to sort the list again.
    if add_missing_nets and bits_in_matrix > 0:
        mask = getMask(start_net.version(), end_net.prefixlen()-bits_in_matrix)
        for ip in sorted_subnets:
            if ip.prefixlen() <= mask.prefixlen():
                continue
            supernet = andIpMask(ip, mask)
            if supernet not in sorted_subnets:
                sorted_subnets.append(supernet)

        sorted_subnets = sort_nets_by_prefixlength(sorted_subnets)

    # build the tree
    for ip in sorted_subnets:
        _insert_into_tree(result, ip)

    return result


def _insert_into_tree(tree, ip):
    for ip_item in tree:
        if ip_item.overlaps(ip):
            _insert_into_tree(tree[ip_item], ip)
            return
    tree[ip] = {}


def get_subnets(network, min_length=None):
    """Retrieves all the subnets of the argument ``network''.

    Arguments:
        ``min_length'': minimum subnet mask length, defaults to
                        network.prefixlen().

    Returns:
        List with IPy.IP objects

    """
    max_length = 128 if network.version() == 6 else 32
    if min_length is None:
        min_length = network.prefixlen()
    assert min_length < max_length
    sql = """
        SELECT netaddr
        FROM prefix
        WHERE family(netaddr)=%s
          AND netaddr << %s
          AND masklen(netaddr) >= %s
          AND masklen(netaddr) < %s
    """
    args = (network.version(), str(network), min_length, max_length)
    db_cursor = db.getConnection('default').cursor()
    db_cursor.execute(sql.strip(), args)
    db_result = db_cursor.fetchall()
    return [IP(i[0]) for i in db_result]


def remove_subnets_with_prefixlength(tree, prefixlen):
    """Generates a new tree from tree, but without subnets with
    prefix length >= prefixlen."""

    def _delete_subnets(tree, limit):
        old_tree = deepcopy(tree)
        for ip in old_tree.keys():
            if ip.prefixlen() >= limit:
                del tree[ip]
        for ip in tree.keys():
            _delete_subnets(tree[ip], limit)
    tree_nets = deepcopy(tree)
    _delete_subnets(tree_nets, prefixlen)
    return tree_nets


def get_subtree(tree, ip):
    """Returns the subtree identified by the arguments ``ip''.
    None if not found."""

    def search_tree(tree, goal):
        """DFS in tree for goal."""
        for node in tree.keys():
            if node == goal:
                return tree[node]
            else:
                result = search_tree(tree[node], goal)
                if result is not None:
                    return result
    return search_tree(tree, ip)


def _is_leaf_node(node):
    if not node.keys():
        return True
    else:
        return False


def get_max_leaf(tree, max_prefix_length=128):
    """Returns the leaf node with highest prefix length.
    If several found; returns the first hit."""

    def _dfs(tree, maxval):
        for node in tree.keys():
            if _is_leaf_node(tree[node]):
                if maxval.prefixlen() < node.prefixlen() <= max_prefix_length:
                    maxval = node
            else:
                result = _dfs(tree[node], maxval)
                if maxval.prefixlen() < result.prefixlen() <= max_prefix_length:
                    maxval = result
        return maxval

    root = next(iter(tree.keys()))
    return _dfs(tree, root)


def extract_subtrees_with_prefix_length(tree, prefixlen):
    """Returns a map of subtrees with length prefixlen. Generated from
    tree"""
    keys = extract_subnets_with_prefix_length(tree, prefixlen)
    result = {}
    for key in keys:
        result[key] = get_subtree(tree, key)
    return result


def extract_subnets_with_prefix_length(tree, prefixlen):
    """Returns a list of subtrees with length prefix lehgth.

    Note: Use extract_subtrees_with_prefix_length if you want the trees
    and not the IPs.

    """
    def _iterator(tree, prefixlen, acc):
        for net in tree.keys():
            if net.prefixlen() == prefixlen:
                acc.append(net)
            if net.prefixlen() < prefixlen:
                _iterator(tree[net], prefixlen, acc)
    acc = []
    _iterator(tree, prefixlen, acc)
    return acc

# -*- coding: utf-8 -*-#
import unittest

from mock import MagicMock
from nav.web.seeddb.forms import get_prefix, tree_pad, create_choices, BOX_CHARS


class PrefixTest(unittest.TestCase):
    SPACES = 2 * BOX_CHARS['SPACE']
    PIPE = BOX_CHARS['VERTICAL'] + BOX_CHARS['SPACE']

    def test_no_ancestors(self):
        self.assertEqual(get_prefix([]), '')

    def test_should_ignore_first_ancestor(self):
        self.assertEqual(get_prefix([False]), '')

    def test_should_map_true_to_two_spaces(self):
        self.assertEqual(get_prefix([False, True]), PrefixTest.SPACES)

    def test_should_map_false_to_pipeish_and_space(self):
        self.assertEqual(get_prefix([False, False]), PrefixTest.PIPE)

    def test_should_map_several_chars(self):
        self.assertEqual(
            get_prefix([False, False, False, False, False]),
            "".join(
                [PrefixTest.PIPE, PrefixTest.PIPE, PrefixTest.PIPE, PrefixTest.PIPE]
            ),
        )

    def test_should_map_mixed_chars(self):
        self.assertEqual(
            get_prefix([False, True, False, True, False]),
            "".join(
                [PrefixTest.SPACES, PrefixTest.PIPE, PrefixTest.SPACES, PrefixTest.PIPE]
            ),
        )


class TreePadTest(unittest.TestCase):
    CORNER = BOX_CHARS['UP_AND_RIGHT'] + BOX_CHARS['SPACE']
    PIPE = BOX_CHARS['VERTICAL_AND_RIGHT'] + BOX_CHARS['SPACE']

    def setUp(self):
        self.string = 'string'

    def test_no_ancestors(self):
        self.assertEqual(tree_pad(self.string, []), self.string)

    def test_one_ancestor_last_child(self):
        """Should only care about its own position"""
        self.assertEqual(
            tree_pad(self.string, [False], last=True), TreePadTest.CORNER + self.string
        )

    def test_one_ancestor_not_last_child(self):
        """Should only care about its own position"""
        self.assertEqual(
            tree_pad(self.string, [False], last=False), TreePadTest.PIPE + self.string
        )

    def test_multiple_ancestors(self):
        result = tree_pad(self.string, [False, True, False, False, True], last=False)
        self.assertTrue(result.endswith(TreePadTest.PIPE + self.string))


class TestCreateChoices(unittest.TestCase):
    def my_setup(self, children=None):
        if children is None:
            children = []

        root = MagicMock(pk='root')
        mock_children = MagicMock()
        mock_children.__iter__ = MagicMock(return_value=iter(children))
        mock_children.count.return_value = len(children)

        root.get_children.return_value = mock_children
        self.root = root

    def test_root_node(self):
        self.my_setup()
        result = create_choices(self.root, [], is_last_child=True)
        self.assertEqual(result, [('root', 'root')])

    def test_one_child(self):
        self.my_setup([MagicMock(pk='child1')])

        result = create_choices(self.root, [], is_last_child=True)
        self.assertEqual(len(result), 2)

    def test_two_children(self):
        self.my_setup([MagicMock(pk='child1'), MagicMock(pk='child2')])

        result = create_choices(self.root, [], is_last_child=True)
        self.assertEqual(len(result), 3)

    def test_two_children_prefix_first(self):
        self.my_setup([MagicMock(pk='child1'), MagicMock(pk='child2')])
        result = create_choices(self.root, [], is_last_child=True)
        self.assertTrue(result[1][1].startswith(TreePadTest.PIPE))

    def test_two_children_prefix_second(self):
        self.my_setup([MagicMock(pk='child1'), MagicMock(pk='child2')])
        result = create_choices(self.root, [], is_last_child=True)
        self.assertTrue(result[2][1].startswith(TreePadTest.CORNER))

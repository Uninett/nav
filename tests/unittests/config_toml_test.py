from unittest import TestCase

from nav.config.toml import TOMLConfigParser, merge_dict_with_defaults


class TestTOMLConfigParserSectionConsistency:
    def test_when_section_is_set_then_contains_should_find_section_keys(self):
        parser = SectionConfig()
        # __getitem__ finds it, but __contains__ does not
        assert parser["alpha"] == 1
        assert "alpha" in parser

    def test_when_section_is_set_then_len_should_count_section_keys(self):
        parser = SectionConfig()
        assert len(parser) == 2

    def test_when_section_is_set_then_iter_should_yield_section_keys(self):
        parser = SectionConfig()
        assert set(parser) == {"alpha", "beta"}

    def test_when_section_is_set_then_keys_should_return_section_keys(self):
        parser = SectionConfig()
        assert set(parser.keys()) == {"alpha", "beta"}

    def test_when_section_is_set_then_values_should_return_section_values(self):
        parser = SectionConfig()
        assert set(parser.values()) == {1, 2}

    def test_when_section_is_set_then_items_should_return_section_items(self):
        parser = SectionConfig()
        assert dict(parser.items()) == {"alpha": 1, "beta": 2}


class TOMLConfigParserTest(TestCase):
    def test_get_method_it_should_use_our_getitem_implementation_not_a_simulated_dict_get(  # noqa: E501
        self,
    ):
        # UserDict was changed in Python 3.12 to not honor its own __getitem__.
        class TestConfig(TOMLConfigParser):
            SECTION = "foo"
            DEFAULT_CONFIG = {
                "foo": {
                    "a": 1,
                    "b": True,
                },
            }

        tc = TestConfig()
        result = tc.get("a")
        self.assertEqual(result, 1)

    def test_merge_with_default_returns_the_combined_output(self):
        class TestConfig(TOMLConfigParser):
            DEFAULT_CONFIG = {
                "a": 1,
                "b": True,
            }

        tc = TestConfig()
        tc._merge_with_default({"b": False, "c": "foo"})
        expected = {
            "a": 1,
            "b": False,
            "c": "foo",
        }
        self.assertEqual(tc.data, expected)

    def test_if_section_is_set_and_no_default_config_get_item_fetches_from_inputted_subdict(  # noqa: E501
        self,
    ):
        class TestConfig(TOMLConfigParser):
            SECTION = "bar"
            DEFAULT_CONFIG = {}

        tc = TestConfig({"bar": {"a": 3}})
        self.assertEqual(tc["a"], 3)

    def test_if_section_is_set_and_no_input_get_item_fetches_from_default_subdict(self):
        class TestConfig(TOMLConfigParser):
            SECTION = "bar"
            DEFAULT_CONFIG = {
                "a": 2,
                SECTION: {
                    "a": 1,
                },
            }

        tc = TestConfig()
        self.assertEqual(tc["a"], 1)


class MergeDictWithDefaultsTests(TestCase):
    def test_golden_path(self):
        data = {
            1: 1,
            2: {
                3: 3,
                6: {7: 7},
                8: None,
            },
            4: 4,
        }
        defaults = {
            0: 0,
            2: {
                3: 0,
                5: 0,
                6: None,
                8: {9: 0},
            },
            4: 0,
        }
        expected = {
            0: 0,
            1: 1,
            2: {
                3: 3,
                5: 0,
                6: {7: 7},
                8: None,
            },
            4: 4,
        }
        result = merge_dict_with_defaults(data, defaults)
        self.assertEqual(result, expected)

    def test_deeper_recursion(self):
        # four levels is the maximum that allauth social auth config needs
        data = {
            1: 1,
            0: {
                2: 2,
                1: {
                    3: 3,
                    2: {
                        3: {
                            4: {6: 6},
                        },
                    },
                },
            },
        }
        defaults = {
            0: {
                1: {
                    2: {
                        3: {
                            4: {5: 0},
                        },
                    },
                }
            },
        }
        expected = {
            1: 1,
            0: {
                2: 2,
                1: {
                    3: 3,
                    2: {
                        3: {
                            4: {
                                5: 0,
                                6: 6,
                            },
                        },
                    },
                },
            },
        }
        result = merge_dict_with_defaults(data, defaults)
        self.assertEqual(result, expected)


class SectionConfig(TOMLConfigParser):
    SECTION = "mysection"
    DEFAULT_CONFIG = {
        "mysection": {
            "alpha": 1,
            "beta": 2,
        },
    }

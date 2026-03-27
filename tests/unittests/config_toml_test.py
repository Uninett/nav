from unittest import TestCase

from nav.config.toml import TOMLConfigParser, merge_dict_with_defaults


class TOMLConfigParserTest(TestCase):
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


class MergeDictWithDefaults(TestCase):
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

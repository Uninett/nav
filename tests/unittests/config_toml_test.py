from tempfile import NamedTemporaryFile
from unittest import TestCase

from nav.config.toml import TOMLConfigParser, merge_dict_with_defaults


class SectionConfig(TOMLConfigParser):
    SECTION = "mysection"
    DEFAULT_CONFIG = {
        "mysection": {
            "alpha": 1,
            "beta": 2,
        },
    }


class TestTOMLConfigParserWhenSectionIsSet(TestCase):
    # There was a backwards incompatible change to UserDict in Python 3.12,
    # so for maximum paranoia make sure they don't change things *again*
    def test_when_no_params_then_self_should_be_the_same_as_the_default_section_dict(
        self,
    ):
        parser = SectionConfig()
        self.assertEqual(parser, parser.DEFAULT_CONFIG[parser.SECTION])

    def test_then_contains_should_find_section_keys(self):
        parser = SectionConfig()
        self.assertIn("alpha", parser)

    def test_then_getitem_should_find_section_values(self):
        parser = SectionConfig()
        # __getitem__ finds it, but __contains__ does not
        self.assertEqual(parser["alpha"], 1)

    def test_then_get_should_find_section_values(self):
        parser = SectionConfig()
        self.assertEqual(parser.get("alpha", None), 1)

    def test_then_len_should_count_section_keys(self):
        parser = SectionConfig()
        self.assertEqual(len(parser), 2)

    def test_then_iter_should_yield_section_keys(self):
        parser = SectionConfig()
        self.assertEqual(set(parser), {"alpha", "beta"})

    def test_then_keys_should_return_section_keys(self):
        parser = SectionConfig()
        self.assertEqual(set(parser.keys()), {"alpha", "beta"})

    def test_then_values_should_return_section_values(self):
        parser = SectionConfig()
        self.assertEqual(set(parser.values()), {1, 2})

    def test_then_items_should_return_section_items(self):
        parser = SectionConfig()
        self.assertEqual(dict(parser.items()), {"alpha": 1, "beta": 2})

    def test_when_no_default_config_then_get_item_fetches_from_inputted_subdict(  # noqa: E501
        self,
    ):
        class TestConfig(TOMLConfigParser):
            SECTION = "bar"
            DEFAULT_CONFIG = {}

        config = TestConfig({"bar": {"a": 3}})
        self.assertEqual(config["a"], 3)


class SectionLessConfig(TOMLConfigParser):
    DEFAULT_CONFIG = {
        "alpha": 1,
        "beta": 2,
    }


class TestTOMLConfigParserWhenSectionIsNotSet(TestCase):
    def test_when_no_parameters_then_should_be_the_same_as_the_default_dict(self):
        config = SectionLessConfig()
        self.assertEqual(config, config.DEFAULT_CONFIG)

    def test_given_an_existing_filename_as_parameter_then_should_merge_default_and_contents_of_file(  # noqa: E501
        self,
    ):
        tomlconfig = b"""
beta = true
gamma = "foo"
"""
        with NamedTemporaryFile() as TF:
            TF.write(tomlconfig)
            TF.flush()
            filename = TF.name
            config = SectionLessConfig(config_file=filename)
            self.assertEqual(config.USED_CONFIG_FILE, filename)

        expected = {
            "alpha": 1,
            "beta": True,
            "gamma": "foo",
        }
        self.assertEqual(config, expected)

    def test_given_a_nonexisting_filename_as_parameter_then_should_be_default(
        self,
    ):
        filename = "vfcgnhjgbvfgnhjgvfgnhjgvfgnhjgvfgnhjmgvfbnhmjgvf"
        config = SectionLessConfig(config_file=filename)
        self.assertEqual(config.USED_CONFIG_FILE, filename)
        self.assertEqual(config, config.DEFAULT_CONFIG)

    def test_merge_with_default_returns_the_combined_output(self):
        config = SectionLessConfig()
        config._merge_with_default({"beta": False, "gamma": "foo"})
        expected = {
            "alpha": 1,
            "beta": False,
            "gamma": "foo",
        }
        self.assertEqual(config.data, expected)


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

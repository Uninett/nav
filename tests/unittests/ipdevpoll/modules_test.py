from configparser import ConfigParser

from nav.ipdevpoll.plugins import modules


class TestGetIgnoredSerials:
    def test_should_return_correct_list_items(self):
        cp = ConfigParser()
        cp.read_string(
            """
        [modules]
        ignored-serials = one   two three
        """
        )

        result = modules.get_ignored_serials(cp)
        assert result == ["one", "two", "three"]

    def test_should_return_default_value_if_none_is_configured(self):
        cp = ConfigParser()
        result = modules.get_ignored_serials(cp)
        assert result == ["BUILTIN"]


class TestModulesPlugin:
    def test_should_load_default_config_without_error(self):
        modules.Modules.on_plugin_load()
        assert modules.Modules.ignored_serials == ['BUILTIN']

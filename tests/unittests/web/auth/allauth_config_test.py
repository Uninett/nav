try:
    import tomllib
except ImportError:
    import tomli as tomllib

from unittest import TestCase
from unittest.mock import patch

from nav.config.toml import TOMLConfigParser
from nav.web.auth.allauth import (
    SocialProviderHelper,
    SocialConfigParser,
    OIDCConfigParser,
)


class SocialProviderHelperTest(TestCase):
    class MyConfig(SocialProviderHelper, TOMLConfigParser):
        _subkey = "bar"
        SECTION = "foo"
        DEFAULT_CONFIG = {SECTION: {}}

    def test_if_providers_exist_get_providers_returns_value_of_subkey(self):
        config = {
            "foo": {
                "bar": 1,
                "xux": 2,
            },
        }
        mc = self.MyConfig(default_config=config)
        result = mc.get_providers()
        self.assertEqual(result, 1)

    def test_if_providers_does_not_exist_return_empty_dict(self):
        mc = self.MyConfig()
        result = mc.get_providers()
        self.assertEqual(result, {})


class SocialConfigParserTests(TestCase):
    def test_generate_SOCIALACCOUNT_PROVIDERS_golden_path(self):
        config_string = """
[social.providers.testprovider1]
client_id = "not.optional"
secret = "not.optional"
scope = ["email"]

[social.providers.testprovider2]
client_id = "not.optional2"
secret = "not.optional2"

[social.providers.testprovider2.settings]
foo = 1  # This is not a valid setting, just for tests!
"""
        config = tomllib.loads(config_string)
        sc = SocialConfigParser(default_config=config)
        expected = {
            "testprovider1": {
                "APP": {
                    "client_id": "not.optional",
                    "secret": "not.optional",
                },
                "SCOPE": ["email"],
            },
            "testprovider2": {
                "APP": {
                    "client_id": "not.optional2",
                    "secret": "not.optional2",
                    "settings": {
                        "foo": 1,
                    },
                },
            },
        }
        result = sc.generate_SOCIALACCOUNT_PROVIDERS()
        self.assertEqual(result, expected)

    def test_if_no_config_generate_SOCIALACCOUNT_PROVIDERS_returns_empty_dict(self):
        sc = SocialConfigParser()
        result = sc.generate_SOCIALACCOUNT_PROVIDERS()
        self.assertEqual(result, {})


class OIDCConfigParserTests(TestCase):
    def test_generate_SOCIALACCOUNT_PROVIDERS_golden_path(self):
        config_string = """
[oidc.idps.testprovider1]
name="Provider 1"
client_id = "not.optional"
secret = "not.optional"
server_url = "https://server1.example.com"

[oidc.idps.testprovider1.settings]
foo = 1  # This is not a valid setting, just for tests!
"""
        config = tomllib.loads(config_string)
        with patch.object(OIDCConfigParser, '_read', return_value=None):
            sc = OIDCConfigParser(default_config=config)
        sc._merge_with_default(config)
        expected = {
            "openid_connect": {
                "OAUTH_PKCE_ENABLED": False,
                "APPS": [
                    {
                        "provider_id": "testprovider1",
                        "name": "Provider 1",
                        "client_id": "not.optional",
                        "secret": "not.optional",
                        "settings": {
                            "server_url": "https://server1.example.com",
                            "uid_field": "sub",
                            "foo": 1,
                        },
                    },
                ],
            },
        }
        result = sc.generate_SOCIALACCOUNT_PROVIDERS()
        self.assertEqual(result, expected)

    def test_if_no_config_generate_SOCIALACCOUNT_PROVIDERS_returns_empty_dict(self):
        sc = OIDCConfigParser()
        result = sc.generate_SOCIALACCOUNT_PROVIDERS()
        self.assertEqual(result, {})

    def test_if_nouid_field_set_fall_back_to_sub(self):
        config_string = """
[oidc.idps.testprovider1]
name="Provider 1"
client_id = "not.optional"
secret = "not.optional"
server_url = "https://server1.example.com"
"""
        config = tomllib.loads(config_string)
        with patch.object(OIDCConfigParser, '_read', return_value=None):
            sc = OIDCConfigParser(default_config=config)
        sc._merge_with_default(config)
        expected = {
            "provider_id": "testprovider1",
            "name": "Provider 1",
            "client_id": "not.optional",
            "secret": "not.optional",
            "settings": {
                "server_url": "https://server1.example.com",
                "uid_field": "sub",
            },
        }
        result = sc.translate_entry_for_provider("testprovider1")
        self.assertEqual(result, expected)

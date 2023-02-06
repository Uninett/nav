from mock import patch
from unittest import TestCase
from nav.jwtconf import JWTConf
from nav.config import ConfigurationError


class TestJWTConf(TestCase):
    def setUp(self):
        pass

    def test_valid_jwks_config_should_pass(self):
        config = u"""
            [nav-config]
            private_key=key
            public_key=key
            name=issuer-name
            [jwks-issuer]
            keytype=JWKS
            aud=nav
            key=www.example.com
            """
        expected_settings = {
            'key': 'www.example.com',
            'type': 'JWKS',
            'claims_options': {
                'aud': {'values': ['nav'], 'essential': True},
            },
        }

        def read_file_patch(self, file):
            return "key"

        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            with patch.object(JWTConf, '_read_file', read_file_patch):
                jwtconf = JWTConf()
                settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings['jwks-issuer'], expected_settings)

    def test_valid_pem_config_should_pass(self):
        config = u"""
            [nav-config]
            private_key=key
            public_key=key
            name=nav-issuer
            [pem-issuer]
            keytype=PEM
            aud=nav
            key=key_path
            """
        pem_key = "PEM KEY"
        expected_settings = {
            'key': pem_key,
            'type': 'PEM',
            'claims_options': {
                'aud': {'values': ['nav'], 'essential': True},
            },
        }

        def read_file_patch(self, file):
            return pem_key

        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            with patch.object(JWTConf, '_read_file', read_file_patch):
                jwtconf = JWTConf()
                settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings['pem-issuer'], expected_settings)

    def test_validate_key_should_raise_error_if_key_is_empty(self):
        jwtconf = JWTConf()
        with self.assertRaises(ConfigurationError):
            jwtconf._validate_key("")

    def test_validate_key_should_allow_non_empty_string(self):
        key = "key"
        jwtconf = JWTConf()
        validated_key = jwtconf._validate_key(key)
        self.assertEqual(validated_key, key)

    def test_validate_audience_should_raise_error_if_audience_is_empty(self):
        jwtconf = JWTConf()
        with self.assertRaises(ConfigurationError):
            jwtconf._validate_audience("")

    def test_validate_audience_should_allow_non_empty_string(self):
        aud = "key"
        jwtconf = JWTConf()
        validated_aud = jwtconf._validate_key(aud)
        self.assertEqual(validated_aud, aud)

    def test_validate_type_should_raise_error_if_type_is_invalid(self):
        jwtconf = JWTConf()
        with self.assertRaises(ConfigurationError):
            jwtconf._validate_type("invalid")

    def test_JWKS_should_be_a_valid_type(self):
        type = "JWKS"
        jwtconf = JWTConf()
        validated_type = jwtconf._validate_type(type)
        self.assertEqual(validated_type, type)

    def test_PEM_should_be_a_valid_type(self):
        type = "PEM"
        jwtconf = JWTConf()
        validated_type = jwtconf._validate_type(type)
        self.assertEqual(validated_type, type)

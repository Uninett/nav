from mock import patch
import mock
from unittest import TestCase
from nav.jwtconf import JWTConf


class TestJWTConf(TestCase):
    def setUp(self):
        pass

    def test_correct_jwks_config_should_pass(self):
        config = u"""
            [jwks-issuer]
            keytype=JWKS
            aud=nav
            key=www.example.com
            """
        expected_settings = {
            'jwks-issuer': {
                'key': 'www.example.com',
                'type': 'JWKS',
                'claims_options': {
                    'aud': {'values': ['nav'], 'essential': True},
                },
            }
        }
        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            jwtconf = JWTConf()
            settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings, expected_settings)

    def test_correct_pem_config_should_pass(self):
        config = u"""
            [pem-issuer]
            keytype=PEM
            aud=nav
            key=key_path
            """
        pem_key = "PEM KEY"
        expected_settings = {
            'pem-issuer': {
                'key': pem_key,
                'type': 'PEM',
                'claims_options': {
                    'aud': {'values': ['nav'], 'essential': True},
                },
            }
        }

        def read_file_patch(self, file):
            return pem_key

        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            with patch.object(JWTConf, '_read_file', read_file_patch):
                jwtconf = JWTConf()
                settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings, expected_settings)

    def test_incorrect_ketype_should_fail(self):
        config = u"""
            [pem-issuer]
            keytype=Fake
            aud=nav
            key=key
            """
        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            jwtconf = JWTConf()
            settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings, dict())

    def test_incorrect_key_should_fail(self):
        config = u"""
            [pem-issuer]
            keytype=JWKS
            aud=nav
            key=
            """
        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            jwtconf = JWTConf()
            settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings, dict())

    def test_incorrect_aud_should_fail(self):
        config = u"""
            [pem-issuer]
            keytype=JWKS
            aud=
            key=key
            """
        with patch.object(JWTConf, 'DEFAULT_CONFIG', config):
            jwtconf = JWTConf()
            settings = jwtconf.get_issuers_setting()
        self.assertEqual(settings, dict())

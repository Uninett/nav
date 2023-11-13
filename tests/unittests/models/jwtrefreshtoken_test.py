import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from nav.models.api import JWTRefreshToken


class TestGenerateAccessToken:
    def test_nbf_should_be_in_the_past(self):
        encoded_token = JWTRefreshToken.generate_access_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['nbf'] < datetime.now().timestamp()

    def test_exp_should_be_in_the_future(self):
        encoded_token = JWTRefreshToken.generate_access_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['exp'] > datetime.now().timestamp()

    def test_iat_should_be_in_the_past(self):
        encoded_token = JWTRefreshToken.generate_access_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['iat'] < datetime.now().timestamp()

    def test_token_type_should_be_access_token(self):
        encoded_token = JWTRefreshToken.generate_access_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['token_type'] == "access_token"


class TestGenerateRefreshToken:
    def test_nbf_should_be_in_the_past(self):
        encoded_token = JWTRefreshToken.generate_refresh_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['nbf'] < datetime.now().timestamp()

    def test_exp_should_be_in_the_future(self):
        encoded_token = JWTRefreshToken.generate_refresh_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['exp'] > datetime.now().timestamp()

    def test_iat_should_be_in_the_past(self):
        encoded_token = JWTRefreshToken.generate_refresh_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['iat'] < datetime.now().timestamp()

    def test_token_type_should_be_refresh_token(self):
        encoded_token = JWTRefreshToken.generate_refresh_token()
        data = JWTRefreshToken._decode_token(encoded_token)
        assert data['token_type'] == "refresh_token"


class TestIsActive:
    def test_should_return_false_if_nbf_is_in_the_future(self, refresh_token_data):
        refresh_token_data['nbf'] = (datetime.now() + timedelta(hours=1)).timestamp()
        refresh_token_data['exp'] = (datetime.now() + timedelta(hours=1)).timestamp()
        encoded_token = JWTRefreshToken._encode_token(refresh_token_data)
        token = JWTRefreshToken(token=encoded_token)
        assert not token.is_active()

    def test_should_return_false_if_exp_is_in_the_past(self, refresh_token_data):
        refresh_token_data['nbf'] = (datetime.now() - timedelta(hours=1)).timestamp()
        refresh_token_data['exp'] = (datetime.now() - timedelta(hours=1)).timestamp()
        encoded_token = JWTRefreshToken._encode_token(refresh_token_data)
        token = JWTRefreshToken(token=encoded_token)
        assert not token.is_active()

    def test_should_return_true_if_nbf_is_in_the_past_and_exp_is_in_the_future(
        self, refresh_token_data
    ):
        now = datetime.now()
        refresh_token_data['nbf'] = (now - timedelta(hours=1)).timestamp()
        refresh_token_data['exp'] = (now + timedelta(hours=1)).timestamp()
        encoded_token = JWTRefreshToken._encode_token(refresh_token_data)
        token = JWTRefreshToken(token=encoded_token)
        assert token.is_active()


class TestExpire:
    def test_should_make_active_token_inactive(self, refresh_token_data):
        now = datetime.now()
        # set claims so the token starts as being active
        refresh_token_data['nbf'] = now - timedelta(hours=1)
        refresh_token_data['exp'] = now + timedelta(hours=1)
        encoded_token = JWTRefreshToken._encode_token(refresh_token_data)
        token = JWTRefreshToken(token=encoded_token)
        token.save = Mock()
        assert token.is_active()
        token.expire()
        assert not token.is_active()


class TestData:
    def test_should_return_accurate_representation_of_token_data(
        self, refresh_token, refresh_token_data
    ):
        token = JWTRefreshToken(token=refresh_token)
        assert token.data() == refresh_token_data


class TestDecodeToken:
    def test_should_return_same_data_as_when_token_was_encoded(
        self, refresh_token, refresh_token_data
    ):
        decoded_data = JWTRefreshToken._decode_token(refresh_token)
        assert decoded_data == refresh_token_data


class TestEncodeToken:
    def test_should_generate_a_known_token_using_the_same_data(
        self, refresh_token, refresh_token_data
    ):
        encoded_token = JWTRefreshToken._encode_token(refresh_token_data)
        assert encoded_token == refresh_token


@pytest.fixture()
def refresh_token_data() -> Dict[Any, str]:
    """Yields the data of the token in the refresh_token fixture"""
    data = {
        "exp": 1516339022,
        "nbf": 1516239022,
        "iat": 1516239022,
        "aud": "nav",
        "iss": "nav",
        "token_type": "refresh_token",
    }
    yield data


@pytest.fixture()
def refresh_token() -> str:
    """Yields a refresh token with data matching the refresh_token_data fixture"""
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1\
MTYzMzkwMjIsIm5iZiI6MTUxNjIzOTAyMiwiaWF0IjoxNTE2MjM5MDIyLCJh\
dWQiOiJuYXYiLCJpc3MiOiJuYXYiLCJ0b2tlbl90eXBlIjoicmVmcmVzaF90\
b2tlbiJ9.LC5YhPTrOQk2q-gPgPHAf9nWF8zjBFBmM6AEh1gSjJgvBdrwqsZ\
7lqsEAQ09IXBrsZ3UhJDkEh5e31Tcp9afk_5f2dLA5zwcayxEbJ7Bj3M0PPb\
D_jz5YWqJ1x9YwROh_iOVtTtVze8079rpF_0LIgbibJjJ1BLrvHLtYhTACTx\
PKfmSJXK60_bg1jRPtlFIilNVdYQ3mnOXjg-9AjsCDH4nzABwiIpAXBR1r-9\
3AZ_ZYxygwctVQpbIJIr0lTntczZ5sRudpK271JHdvLe-iZFz6MpfNIRBJS8\
qawbo_kZmetm6zWmrPDcyC95tYfd2JL8XhEGGpB3nfhQipqG8nQ"
    yield token


@pytest.fixture(scope="module", autouse=True)
def jwtconf_mock(private_key, nav_name) -> str:
    """Mocks the get_nave_name and get_nav_private_key functions for
    the JWTConf class
    """
    with patch("nav.models.api.JWTConf") as _jwtconf_mock:
        instance = _jwtconf_mock.return_value
        instance.get_nav_name = Mock(return_value=nav_name)
        instance.get_nav_private_key = Mock(return_value=private_key)
        yield _jwtconf_mock


@pytest.fixture(scope="module")
def private_key() -> str:
    """Yields a private key in PEM format"""
    key = """-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQCp+4AEZM4uYZKu
/hrKzySMTFFx3/ncWo6XAFpADQHXLOwRB9Xh1/OwigHiqs/wHRAAmnrlkwCCQA8r
xiHBAMjp5ApbkyggQz/DVijrpSba6Tiy1cyBTZC3cvOK2FpJzsakJLhIXD1HaULO
ClyIJB/YrmHmQc8SL3Uzou5mMpdcBC2pzwmEW1cvQURpnvgrDF8V86GrQkjK6nIP
IEeuW6kbD5lWFAPfLf1ohDWex3yxeSFyXNRApJhbF4HrKFemPkOi7acsky38UomQ
jZgAMHPotJNkQvAHcnXHhg0FcWGdohv5bc/Ctt9GwZOzJxwyJLBBsSewbE310TZi
3oLU1TmvAgMBAAECgf8zrhi95+gdMeKRpwV+TnxOK5CXjqvo0vTcnr7Runf/c9On
WeUtRPr83E4LxuMcSGRqdTfoP0loUGb3EsYwZ+IDOnyWWvytfRoQdExSA2RM1PDo
GRiUN4Dy8CrGNqvnb3agG99Ay3Ura6q5T20n9ykM4qKL3yDrO9fmWyMgRJbAOAYm
xzf7H910mDZghXPpq8nzDky0JLNZcaqbxuPQ3+EI4p2dLNXbNqMPs8Y20JKLeOPs
HikRM0zfhHEJSt5IPFQ54/CzscGHGeCleQINWTgvDLMcE5fJMvbLLZixV+YsBfAq
e2JsSubS+9RI2ktMlSKaemr8yeoIpsXfAiJSHkECgYEA0NKU18xK+9w5IXfgNwI4
peu2tWgwyZSp5R2pdLT7O1dJoLYRoAmcXNePB0VXNARqGxTNypJ9zmMawNmf3YRS
BqG8aKz7qpATlx9OwYlk09fsS6MeVmaur8bHGHP6O+gt7Xg+zhiFPvU9P5LB+C0Z
0d4grEmIxNhJCtJRQOThD8ECgYEA0GKRO9SJdnhw1b6LPLd+o/AX7IEzQDHwdtfi
0h7hKHHGBlUMbIBwwjKmyKm6cSe0PYe96LqrVg+cVf84wbLZPAixhOjyplLznBzF
LqOrfFPfI5lQVhslE1H1CdLlk9eyT96jDgmLAg8EGSMV8aLGj++Gi2l/isujHlWF
BI4YpW8CgYEAsyKyhJzABmbYq5lGQmopZkxapCwJDiP1ypIzd+Z5TmKGytLlM8CK
3iocjEQzlm/jBfBGyWv5eD8UCDOoLEMCiqXcFn+uNJb79zvoN6ZBVGl6TzhTIhNb
73Y5/QQguZtnKrtoRSxLwcJnFE41D0zBRYOjy6gZJ6PSpPHeuiid2QECgYACuZc+
mgvmIbMQCHrXo2qjiCs364SZDU4gr7gGmWLGXZ6CTLBp5tASqgjmTNnkSumfeFvy
ZCaDbJbVxQ2f8s/GajKwEz/BDwqievnVH0zJxmr/kyyqw5Ybh5HVvA1GfqaVRssJ
DvTjZQDft0a9Lyy7ix1OS2XgkcMjTWj840LNPwKBgDPXMBgL5h41jd7jCsXzPhyr
V96RzQkPcKsoVvrCoNi8eoEYgRd9jwfiU12rlXv+fgVXrrfMoJBoYT6YtrxEJVdM
RAjRpnE8PMqCUA8Rd7RFK9Vp5Uo8RxTNvk9yPvDv1+lHHV7lEltIk5PXuKPHIrc1
nNUyhzvJs2Qba2L/huNC
-----END PRIVATE KEY-----"""
    yield key


@pytest.fixture()
def public_key() -> str:
    """Yields a public key in PEM format"""
    key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqfuABGTOLmGSrv4ays8k
jExRcd/53FqOlwBaQA0B1yzsEQfV4dfzsIoB4qrP8B0QAJp65ZMAgkAPK8YhwQDI
6eQKW5MoIEM/w1Yo66Um2uk4stXMgU2Qt3LzithaSc7GpCS4SFw9R2lCzgpciCQf
2K5h5kHPEi91M6LuZjKXXAQtqc8JhFtXL0FEaZ74KwxfFfOhq0JIyupyDyBHrlup
Gw+ZVhQD3y39aIQ1nsd8sXkhclzUQKSYWxeB6yhXpj5Dou2nLJMt/FKJkI2YADBz
6LSTZELwB3J1x4YNBXFhnaIb+W3PwrbfRsGTsyccMiSwQbEnsGxN9dE2Yt6C1NU5
rwIDAQAB
-----END PUBLIC KEY-----"""
    yield key


@pytest.fixture(scope="module")
def nav_name() -> str:
    yield "nav"

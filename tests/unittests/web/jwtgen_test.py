import pytest
from unittest.mock import Mock, patch
from datetime import datetime

import jwt

from nav.web.jwtgen import generate_access_token, generate_refresh_token


class TestTokenGeneration:
    """Tests behaviour that should be identical for both access and refresh token generation"""

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_nbf_should_be_in_the_past(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['nbf'] < datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_exp_should_be_in_the_future(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['exp'] > datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_iat_should_be_in_the_past(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['iat'] < datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_aud_should_match_name_from_jwt_conf(self, func, nav_name):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['aud'] == nav_name

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_iss_should_match_name_from_jwt_conf(self, func, nav_name):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['iss'] == nav_name


class TestGenerateAccessToken:
    def test_token_type_should_be_access_token(self):
        encoded_token = generate_access_token()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['token_type'] == "access_token"


class TestGenerateRefreshToken:
    def test_token_type_should_be_refresh_token(self):
        encoded_token = generate_refresh_token()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['token_type'] == "refresh_token"


@pytest.fixture(scope="module", autouse=True)
def jwtconf_mock(private_key, nav_name) -> str:
    """Mocks the get_nav_name and get_nav_private_key functions for
    the JWTConf class
    """
    with patch("nav.web.jwtgen.JWTConf") as _jwtconf_mock:
        instance = _jwtconf_mock.return_value
        instance.get_nav_name = Mock(return_value=nav_name)
        instance.get_nav_private_key = Mock(return_value=private_key)
        yield _jwtconf_mock


@pytest.fixture(scope="module")
def nav_name() -> str:
    yield "nav"


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

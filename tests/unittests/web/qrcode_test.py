from nav.web.utils import generate_qr_code, generate_qr_code_as_string


def test_generate_qr_code_returns_bytes():
    qr_code = generate_qr_code(url="www.example.com", caption="buick.lab.uninett.no")
    assert isinstance(qr_code, bytes)


def test_generate_qr_code_as_string_returns_string():
    qr_code = generate_qr_code_as_string(
        url="www.example.com", caption="buick.lab.uninett.no"
    )
    assert isinstance(qr_code, str)

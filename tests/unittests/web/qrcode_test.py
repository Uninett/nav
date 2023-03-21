import io

from nav.web.utils import generate_qr_code, generate_qr_codes_as_byte_strings


def test_generate_qr_code_returns_byte_buffer():
    qr_code = generate_qr_code(url="www.example.com", caption="buick.lab.uninett.no")
    assert isinstance(qr_code, io.BytesIO)


def test_generate_qr_codes_as_byte_strings_returns_list_of_byte_strings():
    qr_codes = generate_qr_codes_as_byte_strings(
        {"buick.lab.uninett.no": "www.example.com"}
    )
    assert isinstance(qr_codes, list)
    assert isinstance(qr_codes[0], str)

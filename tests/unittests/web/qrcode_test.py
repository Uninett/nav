import io
import zipfile

from nav.web.utils import (
    generate_qr_code,
    generate_qr_codes_as_byte_strings,
    generate_qr_codes_as_zip_response,
)


def test_generate_qr_code_returns_byte_buffer():
    qr_code = generate_qr_code(url="www.example.com", caption="buick.lab.uninett.no")
    assert isinstance(qr_code, io.BytesIO)


def test_generate_qr_codes_as_byte_strings_returns_list_of_byte_strings():
    qr_codes = generate_qr_codes_as_byte_strings(
        {"buick.lab.uninett.no": "www.example.com"}
    )
    assert isinstance(qr_codes, list)
    assert isinstance(qr_codes[0], str)


def test_generate_qr_codes_as_zip_response_should_return_zip_with_correct_filenames():
    response = generate_qr_codes_as_zip_response(
        {
            "buick.lab.uninett.no": "www.example.com",
            "buick2.lab.uninett.no": "www2.example.com",
        }
    )

    buf = io.BytesIO(b"".join(response.streaming_content))
    zip_ = zipfile.ZipFile(buf, "r")

    actual_filenames = set(zip_.namelist())
    expected_filenames = set(["buick.lab.uninett.no.png", "buick2.lab.uninett.no.png"])

    assert actual_filenames == expected_filenames

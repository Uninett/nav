import pytest
from random import shuffle

from nav import natsort


@pytest.mark.parametrize(
    "string,expected",
    [("abc123def", ["abc", 123, "def"]),
     ("123", [123]),
     ("foo-123", ["foo-", 123]),
     ("bar", ["bar"])],
)
def test_natsort_split_should_split_correctly(string, expected):
    assert natsort.split(string) == expected


def test_natsort_splits_can_be_sorted():
    expected = [
        "1 January 1970",
        "1 January 2020",
        "10 January 1970",
        "Tenth of January 1986",
    ]
    data = list(expected)
    for i in range(5):
        shuffle(data)
        result = sorted(data, key=natsort.split)
        assert result == expected

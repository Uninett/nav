from nav.web.geomap.utils import argmax


def test_argmax_plus_one():
    fun = lambda n: n + 1
    assert argmax(fun, [1, 2, 3]) == 3


def test_argmax_negative():
    fun = lambda n: -n
    assert argmax(fun, [1, 2, 3]) == 1

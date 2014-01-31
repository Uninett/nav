from nav.metrics.graphs import (extract_series_name,
                                translate_serieslist_to_regex)


def test_extract_series_name():
    def tester(series, expected):
        assert extract_series_name(series) == expected

    for series, expected in (
        ('scaleToSeconds(nonNegativeDerivative(scale(nav.devices.example-sw_example_org.ports.Po3.ifOutOctets,8)),1)',
         'nav.devices.example-sw_example_org.ports.Po3.ifOutOctets'),

        ('scale(nav.something.*.{in,out}data, 8)',
         'nav.something.*.{in,out}data'),

    ):
        yield "extract_series_name(%r)" % series, tester, series, expected


def test_translate_serieslist_to_regex():
    def tester(series, matches, nonmatches):
        pattern = translate_serieslist_to_regex(series)
        for string in matches:
            assert pattern.match(string), "%s doesn't match %s" % (string,
                                                                   series)

        for string in nonmatches:
            assert not pattern.match(string), "%s matches %s" % (string, series)

    for series, matches, nonmatches in (
        ('plain.jane', ['plain.jane'], ['plain.joe']),

        ('far.out.in.the.*.western.spiral.{arm,leg}',
         ['far.out.in.the.uncharted.western.spiral.arm',
          'far.out.in.the.charted.western.spiral.leg'],
         ['far.out.in.the.forgotten.western.spiral.neck']),

        ('one.two.thre?',
         ['one.two.three', 'one.two.threx'],
         ['one.two.throws'])
    ):
        yield ("test_translate_serieslist_to_regex(%r)" % series,
               tester, series, matches, nonmatches)

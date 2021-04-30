from nav.web.threshold.forms import ThresholdForm


def test_empty_thresholdform_should_not_validate():
    form = ThresholdForm()
    assert not form.is_valid()


def test_thresholdform_with_invalid_period_should_not_validate():
    form = ThresholdForm(
        dict(
            target='some.graphite.metric',
            alert='>15',
            clear='<14',
            period='bad value',
        )
    )
    assert not form.is_valid()


def test_thresholdform_with_invalid_alert_expression_should_not_validate():
    form = ThresholdForm(
        dict(
            target='some.graphite.metric',
            alert='>><15',
            clear='<14',
            period='10m',
        )
    )
    assert not form.is_valid()


def test_filled_thresholdform_should_validate():
    form = ThresholdForm(
        dict(
            target='some.graphite.metric',
            alert='>15',
            clear='<14',
            period='15m',
        )
    )
    assert form.is_valid()

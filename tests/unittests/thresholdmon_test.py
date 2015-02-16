from mock import patch
from nav.thresholdmon import _add_subject_details


def test_non_model_subject_should_not_crash():
    varmap = {}
    with patch("nav.thresholdmon.lookup", return_value="bar"):
        _add_subject_details(None, 'foo', varmap)

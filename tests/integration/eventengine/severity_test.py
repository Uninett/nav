from nav.config import find_config_file

from nav.eventengine.severity import SeverityRules, CONFIG_FILE


class TestThatExampleSeverityRules:
    def test_should_be_valid(self):
        full_path = find_config_file(CONFIG_FILE)
        assert full_path, f"Could not find severity rule config file {CONFIG_FILE}"
        assert SeverityRules.load_from_file(full_path)

#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
import subprocess

import pytest

from nav.startstop import Crontab, CrontabError

DENIED_MESSAGE = b"The user navcron cannot use this program (crontab)\n"


class TestCrontabSave:
    def test_when_crontab_command_fails_then_it_should_raise_error_with_crontab_message(  # noqa: E501
        self, crontab, monkeypatch
    ):
        monkeypatch.setattr(subprocess, "run", _fake_run(1, stderr=DENIED_MESSAGE))
        with pytest.raises(CrontabError) as error:
            crontab.save()
        assert str(error.value).endswith(
            "The user navcron cannot use this program (crontab)"
        )

    def test_when_crontab_command_fails_without_message_then_it_should_raise_error_with_exit_code(  # noqa: E501
        self, crontab, monkeypatch
    ):
        monkeypatch.setattr(subprocess, "run", _fake_run(2))
        with pytest.raises(CrontabError, match="crontab exited with code 2"):
            crontab.save()

    def test_when_crontab_command_succeeds_then_it_should_have_been_fed_the_crontab(  # noqa: E501
        self, crontab, monkeypatch
    ):
        run = _fake_run(0)
        monkeypatch.setattr(subprocess, "run", run)
        crontab["navtest"] = "* * * * * true"
        crontab.save()
        assert b"##block navtest##\n* * * * * true\n##end##" in run.inputs[0]


@pytest.fixture
def crontab(monkeypatch):
    """Returns a Crontab for navcron, loaded as if navcron had an empty crontab"""
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: b"")
    return Crontab("navcron")


def _fake_run(returncode, stderr=b""):
    """Returns a stand-in for subprocess.run that exits with returncode.

    The input of each call is recorded in the stand-in's inputs list.
    """

    def run(args, **kwargs):
        run.inputs.append(kwargs.get("input"))
        return subprocess.CompletedProcess(args, returncode, stderr=stderr)

    run.inputs = []
    return run

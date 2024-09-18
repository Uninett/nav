# Copyright (C) 2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from io import StringIO
from os import makedirs, remove, rmdir, listdir
from os.path import join

import pytest

from nav import config


@pytest.fixture
def mockfile():
    return StringIO(
        "".join(
            [
                '# mock config file\n',
                'foo1=bar1\n',
                'foo2 =  bar2  \n',
                '#foo3=invalid\n',
                'foo4 = bar4 # comment\n',
                '# eof',
            ]
        )
    )


@pytest.fixture
def mockinifile():
    return StringIO(
        "".join(
            [
                '# mock config file\n',
                '[section1]\n',
                'foo1=bar1\n',
                'foo2 =  bar2  \n',
                '[section2] \n',
                '#foo3=invalid\n',
                'foo4 = bar4 \n',
                '# eof',
            ]
        )
    )


def test_read_flat_config(mockfile):
    values = config.read_flat_config(mockfile)
    assert values['foo1'] == 'bar1'
    assert values['foo2'] == 'bar2'
    assert values['foo4'] == 'bar4'
    assert 'foo3' not in values


def test_getconfig(mockinifile):
    values = config.getconfig(mockinifile)
    assert 2 == len(values.keys())
    assert 'section1' in values
    assert 'section2' in values

    assert values['section1']['foo1'] == 'bar1'
    assert values['section1']['foo2'] == 'bar2'
    assert values['section2']['foo4'] == 'bar4'
    assert 'foo3' not in values['section2']


class TestListConfigFiles:
    """Tests for listing the report config files from a given dir"""

    @pytest.mark.parametrize(
        "create_files",
        [["abc.txt", "hello.py", "a.sh", "b.yaml", "c.xml"]],
        indirect=True,
    )
    def test_should_not_include_other_fileendings(self, create_files):
        output_files = []
        gathered_files = config.list_config_files_from_dir(create_files)

        assert gathered_files == output_files

    @pytest.mark.parametrize(
        "create_files",
        [[".abc.conf", ".hello.conf", ".a.conf", ".b.conf", ".c.conf"]],
        indirect=True,
    )
    def test_should_not_include_dot_files(self, create_files):
        output_files = []
        gathered_files = config.list_config_files_from_dir(create_files)

        assert gathered_files == output_files

    @pytest.mark.parametrize(
        "create_files",
        [
            [
                "abc.conf",
                "hello.conf",
                "a.conf",
                "b.conf",
                "_test.conf",
                "c.conf",
            ]
        ],
        indirect=True,
    )
    def test_should_be_sorted_alphabetically(self, create_files):
        filenames = [
            "_test.conf",
            "a.conf",
            "abc.conf",
            "b.conf",
            "c.conf",
            "hello.conf",
        ]
        output_files = [join(create_files, filename) for filename in filenames]
        gathered_files = config.list_config_files_from_dir(create_files)

        assert gathered_files == output_files


#
# Fixtures
#
@pytest.fixture(scope="module")
def create_files(request):
    test_dir = "report.conf.d/"
    makedirs(test_dir)
    for name in request.param:
        open(join(test_dir, name), "x")
    yield test_dir
    for f in listdir(test_dir):
        remove(join(test_dir, f))
    rmdir(test_dir)

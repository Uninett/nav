import os
import contextlib
import subprocess


def test_binaries_are_installed_by_makefile():
    """Verifies that folks remember to add new binaries to the Makefile"""
    mydir = os.path.dirname(__file__)
    bindir = os.path.abspath(os.path.join(mydir, '../../bin'))

    binscripts = _get_binscripts_from_makefile(bindir)

    expected = {f for f in os.listdir(bindir)
                if _is_install_candidate(os.path.join(bindir, f))}

    assert binscripts == expected


####################
# Helper functions #
####################

def _get_binscripts_from_makefile(bindir):
    makefile = os.path.join(bindir, 'Makefile')
    assert os.path.exists(makefile), "No Makefile in the bindir"
    with chdir(bindir):
        output = subprocess.check_output(["make", "-np"]).decode('utf-8')
    output = [l for l in output.splitlines()
              if l.startswith('install-binSCRIPTS:')]
    assert len(output) > 0, "Could not find list of installable scripts"
    _, binscripts = output[-1].split(':', 1)
    binscripts = set(binscripts.strip().split())
    return binscripts


def _is_install_candidate(filename):
    return os.path.isfile(filename) and (
        os.access(filename, os.X_OK) or
        filename.endswith('.py') or
        filename.endswith('.sh')
    )


@contextlib.contextmanager
def chdir(tmpdir):
    curdir = os.getcwd()
    try:
        os.chdir(tmpdir)
        yield
    finally:
        os.chdir(curdir)

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
"""Fails the docs build when a program-output command fails.

sphinxcontrib.programoutput renders the error message or traceback of a
failing command into the page, and only logs it as a warning or error. This
extension makes such failures give the build a non-zero exit status, like
Sphinx's own linkcheck and doctest builders do.
"""

from sphinx.util import logging
from sphinxcontrib.programoutput import Command, program_output

logger = logging.getLogger(__name__)

# programoutput replaces its nodes in a doctree-read handler at the default
# priority (500), so we must inspect them before that. If programoutput ever
# moves its handler before ours, this check silently finds nothing to check.
PRIORITY_BEFORE_PROGRAMOUTPUT = 400


def setup(app):
    app.setup_extension("sphinxcontrib.programoutput")
    app.connect(
        "doctree-read", record_failed_programs, priority=PRIORITY_BEFORE_PROGRAMOUTPUT
    )
    app.connect("env-purge-doc", forget_failures)
    app.connect("env-merge-info", merge_failures)
    app.connect("build-finished", fail_build_on_failures)
    return {"parallel_read_safe": True}


def record_failed_programs(app, doctree):
    """Records the current document as failed if any of its commands fail.

    Results go through programoutput's own cache, so each command that starts
    still runs only once.
    """
    env = app.env
    if any(has_failed(env, node) for node in doctree.findall(program_output)):
        failed_docs(env).add(env.docname)


def forget_failures(app, env, docname):
    failed_docs(env).discard(docname)


def merge_failures(app, env, docnames, other):
    failed_docs(env).update(failed_docs(other))


def fail_build_on_failures(app, exception):
    if exception or not failed_docs(app.env):
        return
    logger.error(
        "program-output commands failed in: %s (their results are cached "
        "between builds, so use sphinx-build -E to rerun them after a fix)",
        ", ".join(sorted(failed_docs(app.env))),
    )
    app.statuscode = 1


def has_failed(env, node):
    command = Command.from_program_output_node(node)
    try:
        returncode, _output = env.programoutput_cache[command]
    except OSError:
        return True
    return returncode != node["returncode"]


def failed_docs(env):
    """Returns the set of documents with failed commands.

    It lives in the build environment, so incremental builds keep it and
    parallel builds merge it.
    """
    if not hasattr(env, "strict_programoutput_failed_docs"):
        env.strict_programoutput_failed_docs = set()
    return env.strict_programoutput_failed_docs

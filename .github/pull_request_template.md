## Scope and purpose

Fixes #<!-- ISSUE-ID -->. Dependent on #<!-- PULL-REQUEST-ID -->. <!-- Reference: https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue -->

<!-- Add a description of what this PR does and why it is needed. If a linked ticket(s)
fully cover it, you can omit this. -->

<!-- remove things that do not apply -->
### This pull request
* adds/changes/removes a dependency
* changes the database
* changes the API


## Contributor Checklist

Every pull request should have this checklist filled out, no matter how small it is.
More information about contributing to NAV can be found in the
[Hacker's guide to NAV](https://nav.readthedocs.io/en/latest/hacking/hacking.html#hacker-s-guide-to-nav).

<!-- Add an "X" inside the brackets to confirm -->
<!-- If not checking one or more of the boxes, please explain why below each or remove the line if not applicable. -->

* [ ] Added a changelog fragment for [towncrier](https://nav.readthedocs.io/en/latest/hacking/hacking.html#adding-a-changelog-entry)
* [ ] Added/amended tests for new/changed code
* [ ] Added/changed documentation
* [ ] Linted/formatted the code with ruff, easiest by using [pre-commit](https://nav.readthedocs.io/en/latest/hacking/hacking.html#pre-commit-hooks-and-ruff)
* [ ] Wrote the commit message so that the first line continues the sentence "If applied, this commit will ...", starts with a capital letter, does not end with punctuation and is 50 characters or less long. See https://cbea.ms/git-commit/
* [ ] Based this pull request on the correct upstream branch: For a patch/bugfix affecting the latest stable version, it should be based on that version's branch (`<major>.<minor>.x`). For a new feature or other additions, it should be based on `master`.
* [ ] If applicable: Created new issues if this PR does not fix the issue completely/there is further work to be done
* [ ] If it's not obvious from a linked issue, described how to interact with NAV in order for a reviewer to observe the effects of this change first-hand (commands, URLs, UI interactions)
* [ ] If this results in changes in the UI: Added screenshots of the before and after
* [ ] If this adds a new Python source code file: Added the [boilerplate header](https://nav.readthedocs.io/en/latest/hacking/hacking.html#python-boilerplate-headers) to that file

<!-- Make this a draft PR if the content is subject to change, cannot be merged or if it is for initial feedback -->

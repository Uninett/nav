#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The describe Mercurial extension, similar to the 'git describe' command.

import re
from mercurial import util, context
from mercurial.i18n import _
from mercurial.node import nullrev, hex, short

def describe(ui, repo, **opts):
    """show most recent tag

    Finds the most recent tag reachable from the current revision.
     
    If the current revision has been tagged, only the tag is
    printed:
     
      v1.2.3
     
    Otherwise the long form is printed which includes the tag, the
    number of commits after the tag, and the node of the current
    changeset:

      v1.2.3-8-2789c05b6c3b
     
    If the closest, tagged revision has multiple tags, each is
    printed on a separate line unless the --single-tag option is
    used, in which case an error is raised.

    If multiple revisions are equally reachable from the root and
    one is on the current branch, it is chosen.  Otherwise each tag
    from each revision is printed on a separate line unless the
    --single-rev option is used, in which case an error is raised.

    If the --prefer-branch option is used, the closest tag on the
    current branch will override closer tags that are reachable but
    not on the same branch.  In the example below, tag A is
    normally chosen since it is closer to the root than B (3
    commits vs 4 commits).  However, if --prefer-branch is used, B
    will be chosen because it is on the the same branch.

            o-A-o
           /     \\
        o-o-B-o-o-o-o <-- root

    The --require-branch option requires the tag to be on the same
    branch.  This is similar to the --prefer-branch option but raises an
    error if no tags are found on the current branch.
    """
    if not repo.local():
        raise util.Abort(_("must be a local repository"))

    if opts['rev']:
        ctx = context.changectx(repo, opts['rev'])
    else:
        ctx = context.workingctx(repo).parents()[0]

    tags, count = _find_closest_tag(ui, repo, ctx, opts)

    uselong = opts['long'] or (count != 0 and not opts['short'])

    if uselong:
        hexfunc = (opts['full'] or ui.debugflag) and hex or short
        node    = hexfunc(ctx.node())
        sep     = opts['spaces'] and ' ' or '-'
        count   = str(count)

        for tag in tags:
            ui.write("%s\n" % sep.join([tag, count, node]))

    else:
        for tag in tags:
            ui.write("%s\n" % tag)
            

def _find_closest_tag(ui, repo, ctx, opts):
    """
    Walks backwards looking for tags using a breadth-first search.

    If successful, returns (tags, level) where level is the distance from the working directory
    (current chageset == 0).  Otherwise an exception is raised.
    """
    prefer  = bool(opts['prefer_branch'])
    require = bool(opts['require_branch'])

    branch = repo.dirstate.branch() # The branch we're currently on

    # The first tags we found.  Normally we'd return as soon as we found tags,
    # but the --prefer-branch option requires us to continue searching in case
    # we find tags on the current branch.
    first_found = []     # each entry is a list of tags from a single revision
    first_level = 0      # the level where we found first_found

    level = 0             # how far from the root are we
    limit = opts['limit'] # how far can we go

    stack = [ ctx ] # revisions to search; when we hit a merge we follow both
                    # parents unless --require-branch was used

    regexp = None
    if opts['regexp']:
        regexp = re.compile(opts['regexp'], re.IGNORECASE)

    while stack:
        current = stack
        stack   = []
        found   = []  # tags found on this level

        if ui.debugflag:
            print '-' * 40

        for ctx in current:
            revbranch = ctx.branch()
            if require and revbranch != branch:
                continue

            tags = ctx.tags()

            if ui.debugflag:
                print ctx.rev(), ' '.join(tags)

            if tags and 'tip' in tags:
                tags = tags[:]     # (copy list; we don't own it)
                tags.remove('tip')

            if tags and regexp:
                # Remove those that don't match the regular expression
                tags = [ tag for tag in tags if regexp.match(tag) ]

            if tags:
                if revbranch == branch:
                    # This is an exact hit on this branch, so use it now.
                    first_found = [ tags ]
                    first_level = level
                    stack = None # break out of outer loop
                    break

                found.append(tags)
                
            # Follow both parents backwards
            for p in ctx.parents():
                # print 'parent:', p
                if p.rev() != nullrev and p not in stack:
                    stack.append(p)

        if found and not first_found:
            first_found = found
            first_level = level

            if not prefer:
                break

        level += 1

        if level == limit:
            raise util.Abort(_("No tags found before limit (%s) reached") % limit)

    if len(first_found) == 0:
        raise util.Abort(_("No tags found on this branch"))

    # first_found is a list with one element for each revision.
    if len(first_found) > 1 and opts['single_rev']:
        raise util.Abort(_("More than one revision matches: %s") % " ".join([ str(m) for m in first_found ]))

    alltags = []
    for tags in first_found:
        alltags.extend(tags)

    if len(alltags) > 1 and opts['single_tag']:
        raise util.Abort(_("More than one tag matches: %s") % " ".join(alltags))

    return alltags, first_level


cmdtable = {
    "describe" : (describe,
                  [ ('l', 'limit',          100,  _('limit how far back to search')),
                    ('r', 'rev',            '',   _('start from specified revision')),
                    ('',  'long',           None, _('output long form always')),
                    ('',  'short',          None, _('output short form always')),
                    ('',  'full',           None, _('output full 40-digit changesetID')),
                    ('',  'spaces',         None, _('separate long form with spaces')),
                    ('',  'prefer-branch',  None, _('prefer tags on this branch')),
                    ('b', 'require-branch', None, _('require tag to be on this branch')),
                    ('',  'single-tag',     None, _('require a single tag')),
                    ('',  'single-rev',     None, _('require a single rev')),
                    ('r', 'regexp',         '',   _('only consider tags that match the regexp')),
                    ],
                  _('hg describe')),
    }
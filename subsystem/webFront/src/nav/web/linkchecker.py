"""
$Id: $

This file is part of the NAV project.
This module contains methods for checking links that are part of the NAV GUI.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Magnar Sveen <magnars@idi.ntnu.no>
"""

import nav

def shouldShow(link, user):
    startsWithHTTP = link.lower()[:7] == 'http://' or link.lower()[:8] == 'https://'
    return startsWithHTTP or nav.auth.hasPrivilege(user, 'web_access', link)

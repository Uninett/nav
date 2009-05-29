# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from mod_python import apache

import nav

from nav.web.preferences import Preferences, Link
from nav.db.navprofiles import Account, Accountnavbar, Navbarlink

def _force_reload_of_user_preferences(req):
  if hasattr(req.session['user'], "preferences"):
    del req.session['user'].preferences
    req.session.save()

def _find_pref_user():
  from nav.web.templates.MainTemplate import MainTemplate
  user = MainTemplate.user
  if user.id == 1:
    # admin changes default user preferences
    user = Account(0)
  return user

def _find_user_preferences(user, req):
  if not hasattr(user, "preferences"):
    # if user preferences is not loaded, it's time to do so
    user.preferences = Preferences()
    conn = nav.db.getConnection('navprofile', 'navprofile')
    prefs = user.getChildren(Accountnavbar)
    if not prefs:
      # if user has no preferences set, use default preferences
      default = Account(0)
      prefs = default.getChildren(Accountnavbar)
    for pref in prefs:
      link = Navbarlink(pref.navbarlink)
      if pref.positions.count('navbar'): # does 'positions'-string contain 'navbar'
        user.preferences.navbar.append(Link(link.name, link.uri))
      if pref.positions.count('qlink1'): # does 'positions'-string contain 'qlink1'
        user.preferences.qlink1.append(Link(link.name, link.uri))
      if pref.positions.count('qlink2'): # does 'positions'-string contain 'qlink2'
        user.preferences.qlink2.append(Link(link.name, link.uri))
    req.session.save() # remember this to next time

def index(req):
  from nav.web.templates.NavbarPreferencesTemplate import NavbarPreferencesTemplate
  template = NavbarPreferencesTemplate()
  template.path = [("Home", "/"), ("Preferences", "/preferences/"), ("Navigation preferences", False)]
  template.title = "Navigation preferences"
  req.content_type = "text/html"
  req.send_http_header()
  user = _find_pref_user()
  if not hasattr(user, "preferences"):
    _find_user_preferences(user, req)
  default = Account(0)
  template.user = user
  template.homemadelinks = user.getChildren(Navbarlink)
  if not user.id == default.id:
    template.defaultlinks = default.getChildren(Navbarlink)
  else:
    template.defaultlinks = False
  accountnavbars = user.getChildren(Accountnavbar)
  if not accountnavbars:
    # if user has no preferences set, make them according to default user
    conn = nav.db.getConnection('navprofile', 'navprofile')
    for pref in default.getChildren(Accountnavbar):
      newpref = Accountnavbar()
      newpref.account = user.id
      newpref.navbarlink = pref.navbarlink
      newpref.positions = pref.positions
      newpref.save()
    conn.commit()
    accountnavbars = user.getChildren(Accountnavbar)
  checked = {}
  for an in accountnavbars:
    checked['KEY' + str(an._getID()[1])] = an.positions
    if (not checked.has_key('qlink1')) and an.positions.count('qlink1'):
      checked['qlink1'] = True
    if (not checked.has_key('qlink2')) and an.positions.count('qlink2'):
      checked['qlink2'] = True
  template.checked = checked
  req.write(template.respond())
  return " "

def newlink(req):
  from nav.web.templates.ChangeLinkTemplate import ChangeLinkTemplate
  template = ChangeLinkTemplate()
  template.path = [("Home", "/"), ("Preferences", "/preferences/"), ("Navigation preferences", False)]
  req.content_type = "text/html"
  req.send_http_header()
  template.link = False
  user = _find_pref_user()
  if user.id == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def editlink(req, id):
  from nav.web.templates.ChangeLinkTemplate import ChangeLinkTemplate
  template = ChangeLinkTemplate()
  template.path = [("Home", "/"), ("Preferences", "/preferences/"), ("Navigation preferences", False)]
  req.content_type = "text/html"
  req.send_http_header()
  conn = nav.db.getConnection('navprofile', 'navprofile')
  template.link = Navbarlink(id)
  user = _find_pref_user()
  if user.id == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def deletelink(req, id):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  user = _find_pref_user()
  link = Navbarlink(id)
  if link.account == user.id or link.account.id == user.id:
    link.delete()
    _force_reload_of_user_preferences(req)
    conn.commit()
  return nav.web.redirect(req, "/preferences/navigation/navigation", seeOther=True)

def saveprefs(req):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  user = _find_pref_user()
  # first delete all preferences
  for oldpref in user.getChildren(Accountnavbar):
    oldpref.delete()
  # then set the new ones
  for key in req.form.keys():
    newpref = Accountnavbar()
    newpref.account = user.id
    newpref.navbarlink = key
    newpref.positions = str(req.form[key])
    newpref.save()
  _force_reload_of_user_preferences(req)
  conn.commit()
  return nav.web.redirect(req, "/", seeOther=True)

def savenewlink(req, name, url, usein):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  user = _find_pref_user()
  newlink = Navbarlink()
  newlink.account = user.id
  newlink.name = name
  newlink.uri = url
  newlink.save()
  if 'navbar qlink1 qlink2'.count(usein):
    newuse = Accountnavbar()
    newuse.account = user.id
    newuse.navbarlink = newlink.id
    newuse.positions = usein
    newuse.save()
  _force_reload_of_user_preferences(req)
  conn.commit()
  return nav.web.redirect(req, "/preferences/navigation/navigation", seeOther=True)

def updatelink(req, id, name, url):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  user = _find_pref_user()
  changedlink = Navbarlink(id)
  if changedlink.account == user.id or changedlink.account.id == user.id:
    changedlink.name = name
    changedlink.uri = url
    changedlink.save()
    _force_reload_of_user_preferences(req)
    conn.commit()
  return nav.web.redirect(req, "/preferences/navigation/navigation", seeOther=True)

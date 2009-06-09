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

from nav.web import redirect
from nav.models.profiles import Account, AccountNavbar, NavbarLink

def _force_reload_of_user_preferences(req):
  if hasattr(req.session['user'], "preferences"):
    del req.session['user']['preferences']
    req.session.save()

def _find_pref_user():
  from nav.web.templates.MainTemplate import MainTemplate
  user = MainTemplate.user
  if user['id'] == 1:
    # admin changes default user preferences
    user = Account.objects.get(id=Account.DEFAULT_ACCOUNT)
  return user

def _find_user_preferences(user, req):
  if not hasattr(user, "preferences"):
    # if user preferences is not loaded, it's time to do so
    user['preferences'] = {
        'navbar': [],
        'qlink1': [],
        'qlink2': [],
    }
    prefs = AccountNavbar.objects.select_related(
        'navbarlink'
    ).filter(account__id=user['id'])
    if not prefs:
      # if user has no preferences set, use default preferences
      prefs = AccountNavbar.objects.select_related(
        'navbarlink'
      ).filter(account__id=Account.DEFAULT_ACCOUNT)
    for pref in prefs:
      link = {
        'name': pref.navbarlink.name,
        'uri': pref.navbarlink.uri,
      }
      if pref.positions.count('navbar'): # does 'positions'-string contain 'navbar'
        user['preferences']['navbar'].append(link)
      if pref.positions.count('qlink1'): # does 'positions'-string contain 'qlink1'
        user['preferences']['qlink1'].append(link)
      if pref.positions.count('qlink2'): # does 'positions'-string contain 'qlink2'
        user['preferences']['qlink2'].append(link)
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

  template.user = user
  template.homemadelinks = NavbarLink.objects.filter(account__id=user['id'])
  if not user['id'] == Account.DEFAULT_ACCOUNT:
    template.defaultlinks = NavbarLink.objects.filter(account__id=Account.DEFAULT_ACCOUNT)
  else:
    template.defaultlinks = False

  accountnavbars = AccountNavbar.objects.filter(account__id=user['id'])
  if not accountnavbars:
    # if user has no preferences set, make them according to default user
    prefs = AccountNavbar.objects.select_related(
        'navbarlink'
    ).filter(account__id=Account.DEFAULT_ACCOUNT)
    for pref in prefs:
      newpref = AccountNavbar(
        account_id=user['id'],
        navbarlink=pref.navbarlink,
        positions=pref.positions
      )
      newpref.save()
    accountnavbars = AccountNavbar.objects.filter(account__id=user['id'])

  checked = {}
  for an in accountnavbars:
    checked['KEY' + str(an.navbarlink.id)] = an.positions
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
  if user['id'] == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def editlink(req, id):
  from nav.web.templates.ChangeLinkTemplate import ChangeLinkTemplate
  template = ChangeLinkTemplate()
  template.path = [("Home", "/"), ("Preferences", "/preferences/"), ("Navigation preferences", False)]
  req.content_type = "text/html"
  req.send_http_header()
  template.link = NavbarLink.objects.get(id=id)
  user = _find_pref_user()
  if user['id'] == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def deletelink(req, id):
  user = _find_pref_user()
  link = NavbarLink.objects.get(id=id)
  if link.account_id == user['id']:
    link.delete()
    _force_reload_of_user_preferences(req)
  return redirect(req, "/preferences/navigation/navigation", seeOther=True)

def saveprefs(req):
  user = _find_pref_user()
  # first delete all preferences
  prefs = AccountNavbar.objects.filter(account=user['id'])
  for oldpref in prefs:
    oldpref.delete()
  # then set the new ones
  for key in req.form.keys():
    newpref = AccountNavbar(
        account_id=user['id'],
        navbarlink_id=key,
        positions=str(req.form[key]),
    )
    newpref.save()
  _force_reload_of_user_preferences(req)
  return redirect(req, "/preferences/navigation/navigation", seeOther=True)

def savenewlink(req, name, url, usein):
  user = _find_pref_user()
  newlink = NavbarLink(
    account_id=user['id'],
    name=name,
    uri=url,
  )
  newlink.save()
  if 'navbar qlink1 qlink2'.count(usein):
    newuse = AccountNavbar(
        account_id=user['id'],
        navbarlink=newlink,
        positions=usein,
    )
    newuse.save()
  _force_reload_of_user_preferences(req)
  return redirect(req, "/preferences/navigation/navigation", seeOther=True)

def updatelink(req, id, name, url):
  user = _find_pref_user()
  changedlink = NavbarLink.objects.get(id=id)
  if changedlink.account_id == user['id']:
    changedlink.name = name
    changedlink.uri = url
    changedlink.save()
    _force_reload_of_user_preferences(req)
  return redirect(req, "/preferences/navigation/navigation", seeOther=True)

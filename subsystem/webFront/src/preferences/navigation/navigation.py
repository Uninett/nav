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

def handler(req):
  from nav.web.templates.NavbarPreferencesTemplate import NavbarPreferencesTemplate
  template = NavbarPreferencesTemplate()
  template.path = [("Frontpage", "/"), ("Preferences", "/preferences/"), ("Navigation preferences", False)]
  template.title = "Navigation preferences"
  req.content_type = "text/html"
  req.send_http_header()
  user = _find_pref_user()
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
    conn.autocommit(1)
    nav.db.navprofiles.setCursorMethod(conn.cursor)
    for pref in default.getChildren(Accountnavbar):
      newpref = Accountnavbar()
      newpref.account = user.id
      newpref.navbarlink = pref.navbarlink
      newpref.positions = pref.positions
      newpref.save()
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
  return apache.OK

def newlink(req):
  from nav.web.templates.ChangeLinkTemplate import ChangeLinkTemplate
  template = ChangeLinkTemplate()
  req.content_type = "text/html"
  req.send_http_header()
  template.link = False
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
  if user.id == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def editlink(req, id):
  from nav.web.templates.ChangeLinkTemplate import ChangeLinkTemplate
  template = ChangeLinkTemplate()
  req.content_type = "text/html"
  req.send_http_header()
  conn = nav.db.getConnection('navprofile', 'navprofile')
  nav.db.navprofiles.setCursorMethod(conn.cursor)
  template.link = Navbarlink(id)
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
  if user.id == 0:
    template.type = "default"
  req.write(template.respond())
  return " "

def deletelink(req, id):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  conn.autocommit(1)
  nav.db.navprofiles.setCursorMethod(conn.cursor)
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
  link = Navbarlink(id)
  if link.account == user.id or link.account.id == user.id:
    link.delete()
    _force_reload_of_user_preferences(req)
  return nav.web.redirect(req, "preferences", seeOther=True)

def saveprefs(req):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  conn.autocommit(1)
  nav.db.navprofiles.setCursorMethod(conn.cursor)
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
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
  return nav.web.redirect(req, "index", seeOther=True)

def savenewlink(req, name, url, usein):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  conn.autocommit(1)
  nav.db.navprofiles.setCursorMethod(conn.cursor)
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
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
  return nav.web.redirect(req, "preferences", seeOther=True)

def updatelink(req, id, name, url):
  conn = nav.db.getConnection('navprofile', 'navprofile')
  conn.autocommit(1)
  nav.db.navprofiles.setCursorMethod(conn.cursor)
  user = _find_pref_user()
  if not user:
    # if no user is defined in the session, redirect to index - same with default user
    return nav.web.redirect(req, "index", seeOther=True)    
  changedlink = Navbarlink(id)
  if changedlink.account == user.id or changedlink.account.id == user.id:
    changedlink.name = name
    changedlink.uri = url
    changedlink.save()
    _force_reload_of_user_preferences(req)
  return nav.web.redirect(req, "preferences", seeOther=True)

"""
$Id: $

This file is part of the NAV project.
This module contains classes used by the user-preferences part of the NAV GUI.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Magnar Sveen <magnars@idi.ntnu.no>
"""

class Preferences:
  def __init__(self):
    self.navbar = []
    self.qlink1 = []
    self.qlink2 = []
    self.hidelogo = 0

class Link:
  def __init__(self, name, uri):
    self.name = name
    self.uri = uri

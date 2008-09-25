# -*- coding: utf-8 -*-
# $Id$
#
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#          Jostein Gogstad <jostein.gogstad@idi.ntnu.no>
#          Jørgen Abrahamsen <jorgen.abrahamsen@uninett.no>
#


from IPy import IP
from mod_python import apache, util
from operator import itemgetter
import copy
import os.path
import psycopg
import re
import string
import urllib
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
from django.core.cache import cache

from nav import db
from nav.report.IPtree import getMaxLeaf, buildTree
from nav.report.generator import Generator, ReportList
from nav.web import redirect
from nav.web import state
from nav.web.URI import URI
from nav.web.templates.MatrixScopesTemplate import MatrixScopesTemplate
from nav.web.templates.ReportListTemplate import ReportListTemplate
from nav.web.templates.ReportTemplate import ReportTemplate, MainTemplate
import nav.path

configFile = os.path.join(nav.path.sysconfdir, "report/report.conf")
configFileLocal = os.path.join(nav.path.sysconfdir, "report/report.local.conf")
frontFile = os.path.join(nav.path.sysconfdir, "report/front.html")

def handler(req):
    uri = req.unparsed_uri
    args = req.args
    nuri = URI(uri)


    # These arguments and their friends will be deleted
    remo = []     

    # Finding empty values
    for key,val in nuri.args.items():
        if val == "":
            remo.append(key)

    # Deleting empty values
    for r in remo:
        if nuri.args.has_key(r):
            del(nuri.args[r])
        if nuri.args.has_key("op_"+r):
            del(nuri.args["op_"+r])
        if nuri.args.has_key("not_"+r):
            del(nuri.args["not_"+r])
    
    if len(remo):
        # Redirect if any arguments were removed
        redirect(req, nuri.make())


    match = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    
    # FIXME: just to avoid noise in the apache log I check for a match, and if
    # not set it to the start page of report tool. The error appearing
    # in the logs when accessing reports: 
    #   AttributeError: 'NoneType' object has no attribute 'group'
    # The weird thing is that the 'if match' is true all the time. So 'match'
    # IS a Match object and doesn't have a 'None'-value. I just don't
    # understand what raises the error referred to in the logs...
    if match:
        reportName = match.group(1)
    else:
        reportName = "report"


    if reportName == "report" or reportName == "index":

        page = MainTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        page.path = [("Home", "/"), ("Report", False)]
        page.title = "Report - Index"
        page.content = lambda:file(frontFile).read()
        req.write(page.respond())
        return apache.OK

    elif reportName == "matrix":

        req.content_type = "text/html"
        req.send_http_header()

        ## Parameterdictionary
        argsdict = {}
        if req.args:
            reqargsplit = urllib.unquote_plus(req.args).split("&")
            if len(reqargsplit):
                for a in reqargsplit:
                    (c,d) = a.split("=")
                    argsdict[c] = d

        scope = None
        if argsdict.has_key("scope") and argsdict["scope"]:
            scope = IP(argsdict["scope"])
        else:
            # Find all scopes in database.
            connection = db.getConnection('webfront','manage')
            database = connection.cursor()
            database.execute("SELECT netaddr FROM prefix INNER JOIN vlan USING (vlanid) WHERE nettype='scope'")
            databasescopes = database.fetchall()
            
            if len(databasescopes) == 1:
                # If there is a single scope in the db, display that
                scope = IP(databasescopes[0][0])
            else:
                # Otherwise, show an error or let the user select from
                # a list of scopes.
                page = MatrixScopesTemplate()
                page.path = [("Home", "/"), ("Report", "/report/"), ("Prefix Matrix",False)]
                page.scopes = []
                for scope in databasescopes:
                    page.scopes.append(scope[0])

                req.write(page.respond())
                return apache.OK

        # If a single scope has been selected, display that.
        if scope is not None:
            show_unused_addresses = True

            if argsdict.has_key("show_unused_addresses"):
                boolstring = argsdict["show_unused_addresses"]
                if boolstring == "True":
                    show_unused_addresses = True
                elif boolstring == "False":
                    show_unused_addresses = False

            matrix = None
            tree = buildTree(scope)

            if scope.version() == 6:
                # Must do import local because of the insane startup cost of
                # importing which slows every run of handler down drastically.
                from nav.report.matrixIPv6 import MatrixIPv6
                end_net = getMaxLeaf(tree)
                matrix = MatrixIPv6(scope,end_net=end_net)

            elif scope.version() == 4:
                # Must do import local because of the insane startup cost of
                # importing which slows every run of handler down drastically.
                from nav.report.matrixIPv4 import MatrixIPv4
                end_net = None

                if scope.prefixlen() < 24:
                    end_net = IP("/".join([scope.net().strNormal(),"27"]))
                    matrix = MatrixIPv4(scope,show_unused_addresses,end_net=end_net)

                else:
                    max_leaf = getMaxLeaf(tree)
                    bits_in_matrix = max_leaf.prefixlen()-scope.prefixlen()
                    matrix = MatrixIPv4(scope,show_unused_addresses,end_net=max_leaf,bits_in_matrix=bits_in_matrix)

            else:
                raise UnknownNetworkTypeException, "version: " + str(scope.version())
            req.write(matrix.getTemplateResponse())

    elif reportName == "reportlist":
        page = ReportListTemplate()
        req.content_type = "text/html"
        req.send_http_header()

        # Default config
        report_list = ReportList(configFile).getReportList()
        map(itemgetter(2), report_list)
        report_list = sorted(report_list, key=itemgetter(2))
        # Local config
        report_list_local = ReportList(configFileLocal).getReportList()
        map(itemgetter(2), report_list_local)
        report_list_local = sorted(report_list_local, key=itemgetter(2))

        name = "Report List"
        name_link = "reportlist"
        page.path = [("Home", "/"), ("Report", "/report/"), (name, "/report/" + name_link)]
        page.title = "Report - " + name
        page.report_list = report_list
        page.report_list_local = report_list_local

        req.write(page.respond())

    else:
        page = ReportTemplate()
        req.content_type = "text/html"
        req.send_http_header()

        gen = Generator()
        
        report = contents = neg = operator = adv = dbresult = None

        # Deleting offset and limit variables from uri so that we would know if
        # it's the same dbresult asked for.
        nuri.setArguments(['offset', 'limit'], '')
        for key,val in nuri.args.items():
            if val == "":
                del nuri.args[key]

        uri_strip = nuri.make()



        if cache.get('report') and cache.get('report')[0] == uri_strip:
            dbresult_cache = cache.get('report')[6]
            (report, contents, neg, operator, adv, dbresult) = gen.makeReport(reportName, configFile, configFileLocal, uri, dbresult_cache)

        else:
            (report, contents, neg, operator, adv, dbresult) = gen.makeReport(reportName, configFile, configFileLocal, uri, None)
            cache.set('report', (uri_strip, report, contents, neg, operator, adv, dbresult), 15 * 60)


        page.report = report
        page.contents = contents
        page.operator = operator
        page.neg = neg

        namename = ""
        if report:
            namename = report.header
            if not namename:
                namename = reportName
            namelink = "/report/"+reportName

        else:
            namename = "Error"
            namelink = False

        page.path = [("Home", "/"), ("Report", "/report/"), (namename,namelink)]
        page.title = "Report - "+namename
        old_uri = req.unparsed_uri
        page.old_uri = old_uri

        page.operators = None
        page.operatorlist = None
        page.descriptions = None

        if adv:
            page.search = True
        else:
            page.search = False

        if report:

            if old_uri.find("?")>0:
                old_uri += "&"
            else:
                old_uri += "?"
            page.old_uri = old_uri

            page.operators = {"eq":"=","like":"~","gt":"&gt;","lt":"&lt;","geq":"&gt;=","leq":"&lt;=","between":"[:]","in":"(,,)"}
            page.operatorlist = ["eq","like","gt","lt","geq","leq","between","in"]
            page.descriptions = {"eq":"equals","like":"contains substring (case-insensitive)","gt":"greater than","lt":"less than","geq":"greater than or equals","leq":"less than or equals","between":"between (colon-separated)","in":"is one of (comma separated)"}

        req.write(page.respond())

    return apache.OK

class UnknownNetworkTypeException(Exception): pass

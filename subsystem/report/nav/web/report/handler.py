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

from mod_python import apache,util

import re,string,copy,urllib
import os.path, nav.path
from nav.web.templates.ReportTemplate import ReportTemplate,MainTemplate
from nav.web.templates.MatrixScopesTemplate import MatrixScopesTemplate
from nav.web.URI import URI
from nav.web import redirect
#from nav.report.matrix import Matrix
from nav.report.generator import Generator,ReportList
from nav.report.matrixIPv4 import MatrixIPv4
from nav.report.matrixIPv6 import MatrixIPv6
from nav.report.IPtree import getMaxLeaf,buildTree
from nav.report.metaIP import MetaIP
from IPy import IP

configFile = os.path.join(nav.path.sysconfdir, "report/report.conf")
frontFile = os.path.join(nav.path.sysconfdir, "report/front.html")

def handler(req):
    uri = req.unparsed_uri
    args = req.args
    nuri = URI(uri)

    remo = [] # these arguments and their friends will be deleted

    for key,val in nuri.args.items():
        if val == "" or key=="r4g3n53nd":
            remo.append(key)

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

    r = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    reportName = r.group(1)

    if reportName == "report" or reportName == "index":

        page = MainTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        list = []
        page.path = [("Home", "/"), ("Report", False)]
        page.title = "Report - Index"
        if req.args and req.args.find("sort=alnum")>-1:
            sortby = "<a href=\"index\">Logical order</a> | Alphabetical order"
            list.sort()
        else:
            sortby = "Logical order | <a href=\"index?sort=alnum\">Alphabetical order</a>"

        w = "<ul>"
        for (description,key) in list:
            w += "<li><a href="+key+">"+description+"</a></li>"
        w += "</ul>"

        #req.write(w+sortby)
        page.content = lambda:file(frontFile).read()
        #lambda:w+sortby
        req.write(page.respond())
        return apache.OK

    elif reportName == "matrix":

        req.content_type = "text/html"
        req.send_http_header()

        ## parameterdict
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
            from nav import db
            import psycopg
            connection = db.getConnection('webfront','manage')
            database = connection.cursor()
            database.execute("select netaddr from prefix inner join vlan using (vlanid) where nettype='scope'")

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
                end_net = getMaxLeaf(tree)
                matrix = MatrixIPv6(scope,end_net=end_net)
            elif scope.version() == 4:
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

            # Invalidating the MetaIP cache to get rid of processed data.
            MetaIP.invalidateCache()


    else:
        page = ReportTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        gen = Generator()
        (report,contents,neg,operator,adv) = gen.makeReport(reportName,configFile,uri)

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

def selectoptiondraw(name,elementlist,elementdict,selectedvalue="",descriptiondict=None):
    ret = '<select name="%s">'%name
    for element in elementlist:
        if element == selectedvalue:
            selected = " selected"
        else:
            selected = ""
        description = ""
        if descriptiondict.has_key(element):
            description = ' title="%s"' %(descriptiondict[element])
        ret += '<option value="%s"%s%s>%s</option>'%(element,description,selected,elementdict[element])
    ret+= '</selected>'
    return ret

class UnknownNetworkTypeException(Exception): pass

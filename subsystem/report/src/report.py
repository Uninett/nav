from mod_python import apache,util

import re,string,copy,pprint
import os.path, nav.path
from nav.web.templates.ReportTemplate import ReportTemplate,MainTemplate
from nav.web.templates.MatrixTemplate import MatrixTemplate

from Generator import Generator,ReportList
from Matrix import Matrix

configFile = os.path.join(nav.path.sysconfdir, "report/report.conf")
frontFile = os.path.join(nav.path.sysconfdir, "report/front.html")

def handler(req):
    uri = req.unparsed_uri
    args = req.args

    r = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    reportName = r.group(1)

    if reportName == "report" or reportName == "index":
        
        page = MainTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        list = ReportList(configFile).getReportList()
        page.path = [("Home", "/"), ("Report", False)]
        page.title = "Report - Index"
        #req.write(pprint.pformat(req.args))
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

        page = MatrixTemplate()
        req.content_type = "text/html"
        req.send_http_header()

        matrix = Matrix()
        matrix.makeMatrix()

        page.path = [("Home", "/"), ("Report", "/report/"), ("Prefix Matrix",False)]
        page.start = matrix.start
        page.end = matrix.end
        page.unntak = matrix.unntak
        page.big_net_rowspan = matrix.big_net_rowspan
        page.colspan = {20: 8, 21: 8,  22: 8, 23: 8, 24: 8, 25: 4, 26: 2, 27: 1}
        page.subnet = matrix.subnet
        page.bnet = matrix.bnet
        page.network = matrix.network
        page.numbers = matrix.numbers
        req.write(page.respond())

    else:
        page = ReportTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        gen = Generator()
        (report,contents,neg,operator,adv) = gen.makeReport(reportName,configFile,uri)
        #req.write(pprint.pformat(neg))
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

            if adv:
##                req.write("<a href=\""+old_uri+"adv=\">Close Search</a>")
##                req.write('<h2>Advanced Search</h2><form action="" method="get"><table>')
                page.operators = {"eq":"=","like":"~","gt":"&gt;","lt":"&lt;","geq":"&gt;=","leq":"&lt;=","between":"[:]","in":"(,,)"}
                page.operatorlist = ["eq","like","gt","lt","geq","leq","between","in"]
                page.descriptions = {"eq":"equals","like":"contains substring (case-insensitive)","gt":"greater than","lt":"less than","geq":"greater than or equals","leq":"less than or equals","between":"between (colon-separated)","in":"is one of (comma separated)"}
##                 for a in report.form:
##                     operators = {"eq":"=","like":"~","gt":"&gt;","lt":"&lt;","geq":"&gt;=","leq":"&lt;=","between":"[:]","in":"(,,)"}
##                     operatorlist = ["eq","like","gt","lt","geq","leq","between","in"]
##                     descriptions = {"eq":"equals","like":"contains substring (case-insensitive)","gt":"greater than","lt":"less than","geq":"greater than or equals","leq":"less than or equals","between":"between (colon-separated)","in":"is one of (comma separated)"}
##                     value = ""
##                     nott = ""
##                     operat = ""
##                     if contents.has_key(a.raw):
##                         value = contents[a.raw]
##                         if operator.has_key(a.raw):
##                             operat = operator[a.raw]
##                         if neg.has_key(a.raw):
##                             nott = 'checked="1"'
##                     select = selectoptiondraw(a.raw+"_op",operatorlist,operators,operat,descriptions)
##                     req.write('<tr><td><label for="%s">%s</label></td><td><input type="checkbox" name="%s_not" id="%s_not" %s></td><td><label for="%s_not">not</label></td><td>%s</td><td><input type="text" name="%s" id="%s" value="%s"></td></tr>'%(a.raw,a.title,a.raw,a.raw,nott,a.raw,select,a.raw,a.raw,value))

##                 req.write('<tr><td></td><td></td><td><input type="hidden" name="adv" value="1"/></td><td><input type="submit" name="r4g3n53nd" value="Send"/></table></form>')

##                 req.write("<font size=1>The operators are used like this")
##                 req.write('<ul><li>= : "equals" (enter null for empty string)</li><li>~ : "case insensitive search (* wildcards)"</li><li>[:] : "between", takes two colon-separated arguments</li><li>(,,) : "is one of", takes a comma-separated list of any size as argument. </li></ul><p><,>,<= and >= needs no explanation. </p><p> All these operators may be negated by clicking the "not" checkbox.</p></font>')
##             else:
##                 req.write("<a href=\""+old_uri+"adv=1\">Advanced Search</a>")
##                 #req.write("<a href=\"javascript:openpopup()\">Advanced Search 2</a>")

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

from mod_python import apache,util

import re,string,copy,pprint

from nav.web.templates.ReportTemplate import ReportTemplate,MainTemplate

from Generator import Generator,ReportList

configFile = "/usr/local/nav/navme/apache/webroot/report/ragen.conf"

def handler(req):
    uri = req.unparsed_uri
    args = req.args

    r = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    reportName = r.group(1)

##     if reportName == "argumentRewriter":

##         keep_blank_values = True
##         form = util.FieldStorage(req,keep_blank_values)

##         arguments = []
##         for a in range(len(form['sequence'])):
##             _not = ""
##             notstring = "not_%s"%form['sequence'][a]
##             if form.has_key(notstring):
##                 _not = "not"

##             _contents = ""
##             if form['contents'][a] == "null":
##                 _operator = "null"
##                 arguments.append(form['sequence'][a]+"="+_not+_operator+_contents)
##             elif form['contents'][a]:
##                 _operator = form['operator'][a]
##                 _contents = "("+form['contents'][a]+")"
##                 arguments.append(form['sequence'][a]+"="+_not+_operator+_contents)

##         uri = form['report']+"?"+"&".join(arguments)
##         #req.write(str(arguments))
##         req.headers_out.add("Location", uri)
##         raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

    #el
    if reportName == "report" or reportName == "index":
        
        page = MainTemplate()
        req.content_type = "text/html"
        req.send_http_header()

        list = ReportList(configFile).getReportList()

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
        page.content = lambda:w+sortby
        req.write(page.respond())
        return apache.OK
        
    else:
        page = ReportTemplate()
        req.content_type = "text/html"
        req.send_http_header()
        gen = Generator()
        (report,contents,neg,operator) = gen.makeReport(reportName,configFile,uri)
        #req.write(pprint.pformat(neg))
        page.report = report
        req.write(page.respond())
        req.write('<form action="" method="get"><table>')
        for a in report.form:
            operators = {"eq":"=","like":"~","gt":"&gt;","lt":"&lt;","geq":"&gt;=","leq":"&lt;=","between":"[:]","in":"(,,)"}
            operatorlist = ["eq","like","gt","lt","geq","leq","between","in"]
            descriptions = {"eq":"equals","like":"contains substring (case-insensitive)","gt":"greater than","lt":"less than","geq":"greater than or equals","leq":"less than or equals","between":"between (colon-separated)","in":"is one of (comma separated)"}
            value = ""
            nott = ""
            operat = ""
            if contents.has_key(a.raw):
                value = contents[a.raw]
                if operator.has_key(a.raw):
                    operat = operator[a.raw]
                if neg.has_key(a.raw):
                    nott = 'checked="1"'
            select = selectoptiondraw(a.raw+"_op",operatorlist,operators,operat,descriptions)
            req.write('<tr><td><label for="%s">%s</label></td><td><input type="checkbox" name="%s_not" id="%s_not" %s></td><td><label for="%s_not">not</label></td><td>%s</td><td><input type="text" name="%s" id="%s" value="%s"></td></tr>'%(a.raw,a.title,a.raw,a.raw,nott,a.raw,select,a.raw,a.raw,value))

        req.write('<tr><td></td><td></td><td></td><td><input type="submit" name="r4g3n53nd" value="Send"/></table></form>')

        req.write("The operators are used like this")
        req.write('<ul><li>= : "equals" (enter null for empty string)</li><li>~ : "case insensitive search (* wildcards)"</li><li>[:] : "between", takes two colon-separated arguments</li><li>(,,) : "is one of", takes a comma-separated list of any size as argument. </li></ul><p><,>,<= and >= needs no explanation. </p><p> All these operators may be negated by clicking the "not" checkbox.</p>')

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

from mod_python import apache

import re,string,copy

from ReportTemplate import ReportTemplate
from Generator import Generator

configFile = "/home/gartmann/public_html/ragen.conf"

def handler(req):
    page = ReportTemplate()
    req.content_type = "text/html"
    req.send_http_header()
    uri = req.unparsed_uri
    args = req.args

    r = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    reportName = r.group(1)
    gen = Generator()
    report = gen.makeReport(reportName,configFile,uri)
    #req.write(str(gen.config.sql_from))
    page.report = report
    req.write(page.respond())
    return apache.OK





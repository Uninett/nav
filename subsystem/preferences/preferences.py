from mod_python import apache,util

from nav.web.templates.MainTemplate import MainTemplate

frontFile = "/usr/local/nav/navme/apache/webroot/preferences/list.html"

def handler(req):
    page = MainTemplate()
    req.content_type = "text/html"
    req.send_http_header()
    page.path = [("Frontpage", "/"), ("Preferences", False)]
    page.title = "Preferences"
    page.content = lambda:file(frontFile).read()
    page.additionalCSS = lambda:"""
    td.name {
       padding: 3px 10px 6px 10px;
       vertical-align: top;
       background-image:url('/images/form/fill-submit.gif');
       background-color:#ddf;
       border: 1px solid black;
    }

    td.description {
       padding: 3px 10px 6px 10px;
       border: 1px solid #ccc;
    }
    """
    req.write(page.respond())
    return apache.OK

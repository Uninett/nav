from nav import users
import base64
import re
import sys

def setAuthHeader(req):
    """Set the request's err headers to indicate that authentication
    is needed from the client"""
    
    realm = 'NAV Restricted Area'
    challenge = "Basic realm=\"%s\"" % (realm)
    req.err_headers_out['WWW-Authenticate'] = challenge


def processAuthentication(req):
    """Process whatever authentication the client may have supplied in
    its request. If the client can be authenticated, a valid User
    object is returned.  If the authentication did not check out, we
    raise an Apache exception (HTTP_UNAUTHORIZED).  If no
    authentication was supplied, None is returned."""
    
    from mod_python import apache
    login = ''
    passwd = ''

    # Did the client supply its credentials with the request?
    if req.headers_in.has_key('Authorization'):
        try:
            auth = req.headers_in['Authorization'][6:]
            auth = base64.decodestring(auth)
            login, passwd = auth.split(':', 1)
        except:
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

        user = users.loadUser(login)
        if user and user.authenticate(passwd):
            return user
        else:
            # If the supplied authentication did not check out, the
            # request was completely unauthorized, and we bail out
            # here.
            setAuthHeader(req)
            raise apache.SERVER_RETURN, apache.HTTP_UNAUTHORIZED
    else:
        return None


def checkAuthorization(user, uri):
    """Check whether the given user object is authorized to access the
    specified URI)"""

    regex = re.compile('\.pl$')
    if regex.search(uri) and not user:
        return False
    else:
        return True
    

def headerparserhandler(req):
    """This is a header parser handler for Apache.  It will parse all
    requests to NAV and perform authentication and authorization
    checking.  Unauthorized access to resources will be dismissed at
    an early stage"""
    
    from mod_python import apache
    # just some debug output
    req.headers_out['X-Debug'] = "uri=%s" % req.uri
    req.err_headers_out['X-Debug'] = "uri=%s" % req.uri

    user = processAuthentication(req)
    if checkAuthorization(user, req.uri):
        return apache.OK
    else:
        setAuthHeader(req)
        raise apache.SERVER_RETURN, apache.HTTP_UNAUTHORIZED

def reloadEverything():
    # Quick-n-dirty development-hack to reload everything
    for module in sys.modules.values():
        try:
            reload(module)
        except:
            pass


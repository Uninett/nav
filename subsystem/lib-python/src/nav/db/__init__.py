"""
$Id: x1$

Database functionality for NAV.
"""
import psycopg
from nav import config

db = None
driver = psycopg

def escape(string):
    return str(psycopg.QuotedString(string))

def getConnection(scriptName, database='nav'):
    """
    Returns an open database connection, as configured in db.conf for
    the given scriptName.
    """
    conf = config.readConfig('db.conf')
    dbname = conf['db_%s' % database]
    user   = conf['script_%s' % scriptName]
    pw     = conf['userpw_%s' % user]

    connection = psycopg.connect('host=%s dbname=%s user=%s password=%s' %
                                 (conf['dbhost'], dbname, user, pw))
    return connection

def setDefaultConnection(conn):
    global db, cursor
    db = conn
    cursor = db.cursor
#    db.autocommit(1)

###### Initialization ######

if not db:
    setDefaultConnection(getConnection('default'));


"""
$Id: $

Database functionality for NAV.
"""
import psycopg
from nav import config

# MUST read config and scriptname!!! =)))

db = psycopg.connect(host="localhost", user="manage", password="eganam", database="manage")
db.autocommit(1)
cursor = db.cursor


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

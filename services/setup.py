import re,getopt,sys,config,database,psycopg,os
from job import jobmap

class Service:
	def __init__(self,id,active,sysname,handler,args):
		self.id = id
		self.active = active
		self.sysname = sysname
		self.handler = handler
		self.args = args
	def __cmp__(self,obj):
		if self.id == 'new':
			return -1
		else:
			i = int(self.id)
			j = type(obj) == int and obj or int(obj.id)
			return i.__cmp__(j)
	def __repr__(self):
		return "%-8s,%-8s,%-20s,%-10s,%s" % (`self.id`,`self.active`,`self.sysname`,`self.handler`,self.args)
def parseLine(line):
	try:
		id,active,sysname,handler,args = eval(line.lower())
	except ValueError:
		msg = "tuple of wrong size: (%s)" % line
		raise TypeError(msg)
	if not (id == 'new' or str(id).isdigit()):
		msg = "should be 'new' or a number: (%s)" % id
		raise TypeError(msg)
	if not active in ('false','true'):
		msg = "should be 'true' or 'false': (%s)" % active
		raise TypeError(msg)
	if handler not in jobmap:
		msg = "no such handler/type: (%s)" % handler
		raise TypeError(msg)
	if not type(args) == dict:
		msg = "should be a dict: (%s)" % args
		raise TypeError(msg)
	return Service(id,active,sysname,handler,args)
def help():
	print """ - Setup -

	valid options:
		-h shows help
		-f file, default services.conf
		-c file, default db.conf
"""
def fromFile(file):
	new = []
	for i in open(file).read().split('\n'):
		i = i.split('#')[0]
		if i:
			service = parseLine(i)
			new += [service]
	return new
class DB:
	def __init__(self,conf):
		self.conf = conf
	def connect(self):
		conf = self.conf
		self.db = psycopg.connect("host = %s user = %s dbname = %s password = %s" % (conf["dbhost"],"manage",conf["db_nav"],conf["userpw_manage"]))
		self.db.autocommit(1)
		self.sysboks()
	def sysboks(self):
		s = self.query('select sysname,boksid from boks')
		self.boks = dict(s)
	def query(self,querystring):
		s = self.db.cursor()
		s.execute(querystring)
		return s.fetchall()
	def fromDB(self):
		i = self.query('SELECT serviceid,sysname FROM service NATURAL JOIN boks')
		return dict(i)
	def delete(self,serviceid):
		s = self.db.cursor()
		s.execute('DELETE FROM service WHERE serviceid = %s' % serviceid)
	def updateservice(self,service):
		s = self.db.cursor()
		s.execute("UPDATE service SET boksid = %s, active = %s, handler = '%s' WHERE serviceid = %s" % (self.boks[service.sysname], service.active, service.handler, service.id))
		self.insertargs(service)
	def insertservice(self,service):
		if service.id != 'new':
			raise Exception('EASDFG reality disfunction!!112')
		s = self.db.cursor()
		next = self.query("select nextval('service_serviceid_seq')")[0][0]
		s.execute("INSERT INTO service (serviceid,boksid,active,handler) VALUES (%s,%s,%s,'%s')" % (next, self.boks[service.sysname], service.active, service.handler))
		self.insertargs(service)
		service.id = next
		return next
	def insertargs(self,service):
		s = self.db.cursor()
		s.execute('DELETE FROM serviceproperty WHERE serviceid = %s' % service.id)
		for prop,value in service.args.items():
			s.execute("INSERT INTO serviceproperty (serviceid,property,value) values (%s,'%s','%s')" % (service.id,prop,value))
def newFile(file,conf):
	conf = config.config(conf)
	db = DB(conf)
	db.connect()

	database.db = db.db
	jobs  = db.fromDB()

	services = []

	for i in database.getJobs(0):
		serviceid = i.getServiceid()
		active = (i.active and 'true') or 'false'
		sysname = jobs[serviceid]
		handler = i.getType()
		args = i.getArgs()
		
		new = Service(serviceid,active,sysname,handler,args)
		services += [new]
	services.sort()
	header = '#id     active   sysname              handler    args'
	print header
	for i in services:
		print i
	
		
def main(file,conf):
	conf = config.config(conf)
	db = DB(conf)

	print 'parsing file'
	new = {}
	for i in fromFile(file):
		new[i.id] = i
	print new

	print 'fetching services from db'
	db.connect()
	result = db.fromDB()
	print result

	delete = []
	for i in result:
		if i not in new:
			delete += [i]
		elif new[i].sysname != result[i]:
			msg = 'serviceid and sysname do not match: (%s,%s) should be (%s,%s)' % (i,new[i],i,result[i])
			raise TypeError(msg)
	for i in new.values():
		if i.sysname not in db.boks:
			msg = 'sysname not found: (%s)' % i.sysname
			raise TypeError(msg)

	print 'to be deleted:', delete
	for i in delete:
		db.delete(i)
	print 'to be added/updateded:', new
	for i in new.values():
		if i.id == 'new':
			db.insertservice(i)
		else:
			db.updateservice(i)
	keys = new.keys()
	keys.sort()
	for i in keys:
		print new[i]
	
if __name__=='__main__':
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hnf:c:')
		opts = dict(opts)
		if '-h' in opts:
			help()
			sys.exit()
		file = opts.get('-f','services.conf')
		conf = opts.get('-c','db.conf')
		if '-n' in opts:
			newFile(file,conf)
		else:
			for i in (file,conf):
				if not os.path.exists(i):
					msg = 'cant find file: ' + i
					raise IOError(msg)
			main(file,conf)
		sys.exit(0)
	except (getopt.error):
		pass
	help()
	sys.exit(2)

"""
$Id: setup.py,v 1.5 2002/06/28 09:36:54 erikgors Exp $
"""
import os
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/handler")
import re,getopt,sys,config,database,psycopg, jobmap

HEADER = '#id     active   sysname              handler    args'

mapper = jobmap.jobmap()

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
	def __hash__(self):
		return self.id.__hash__()
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
	if handler not in mapper:
		msg = "no such handler/type: (%s)" % handler
		raise TypeError(msg)
	if not type(args) == dict:
		msg = "should be a dict: (%s)" % args
		raise TypeError(msg)
	return Service(id,active,sysname,handler,args)

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
		database.db = self.db
	def sysboks(self):
		s = self.query('select sysname,boksid from boks')
		self.boks = dict(s)
	def query(self,querystring):
		s = self.db.cursor()
		s.execute(querystring)
		return s.fetchall()
	def fromDB(self):
		services = []

		for i in database.getJobs(0):
			serviceid = i.getServiceid()
			active = (i.active and 'true') or 'false'
			#active = 'true'
			boksid = i.getBoksid()
			for j in self.boks:
				if self.boks[j] == boksid:
					sysname = j
					break
			handler = i.getType()
			args = i.getArgs()
			
			new = Service(serviceid,active,sysname,handler,args)
			services += [new]
		services.sort()
		return services

	def delete(self,serviceid):
		print "serviceid: %s" % serviceid
		s = self.db.cursor()
		s.execute("DELETE FROM service WHERE serviceid = '%s'" % serviceid.id)
	def updateservice(self,service):
		s = self.db.cursor()
		s.execute("UPDATE service SET boksid = %s, active = %s, handler = '%s' WHERE serviceid = %s" % (self.boks[service.sysname], service.active, service.handler, service.id))
		self.insertargs(service)
	def insertservice(self,service):
		if service.id != 'new':
			raise Exception('EASDFG reality disfunction!!112')
		s = self.db.cursor()
		next = self.query("select nextval('service_serviceid_seq')")[0][0]
#		try:
		s.execute("INSERT INTO service (serviceid,boksid,active,handler) VALUES (%s,%s,%s,'%s')" % (next, self.boks[service.sysname], service.active, service.handler))
#		except KeyError: # dette skal ikke kunne skje
#			print "Boksen er sikkert ikke registrert: %s" % service.sysname
		service.id = next
		self.insertargs(service)
		#return next
	def insertargs(self,service):
		s = self.db.cursor()
		s.execute('DELETE FROM serviceproperty WHERE serviceid = %s' % service.id)
		for prop,value in service.args.items():
			s.execute("INSERT INTO serviceproperty (serviceid,property,value) values (%s,'%s','%s')" % (service.id,prop,value))
def newFile(file,conf):
	conf = config.config(conf)
	db = DB(conf)
	db.connect()

	print 'fetching services from db'
	services = db.fromDB()

	print 'creating ' + file
	file = open(file,'w')
	file.write(HEADER + '\n')
	for i in services:
		file.write('%s\n' % i)
	
		
def main(file,conf):
	conf = config.config(conf)
	db = DB(conf)

	print 'parsing file'
	new = {}
	newentries = []
	for i in fromFile(file):
		if i.id=="new":
			newentries.append(i)
		else:
			new[i.id] = i
	
	print "in file: %i" % (len(new) + len(newentries))
	print "Newentries: %i" % len(newentries)
	print 'fetching services from db'
	db.connect()
	result = db.fromDB()
	print "in db: %i" % len(result)

	delete = []
	for i in result:
		if i not in new:
			delete += [i]
		elif new[i.id].sysname != i.sysname:
			msg = 'serviceid and sysname do not match: (%s,%s) should be (%s,%s)' % (i,new[i],i,result[i])
			raise TypeError(msg)
	for i in new.values():
		if i.sysname not in db.boks:
			msg = 'sysname not found: (%s)' % i.sysname
			raise TypeError(msg)
	if delete:
		print 'to be deleted:'
		for i in delete:
			print i
		s = 0
		while s not in ('yes','no'):
			print '\nare you sure you want to delete? (yes/no)'
			s = raw_input()
		if s == 'no':
			print 'quitting'
			sys.exit(1)
		for i in delete:
			db.delete(i)
	print 'updating db'

	for i in new.values():
#		print "updateing: %s" % i
		if i.id == 'new':
			print "This shouldn't happen"
		else:
			db.updateservice(i)
	for i in newentries:
		db.insertservice(i)

	keys = new.keys()
	keys.sort()

	print 'creating ' + file
	file = open(file,'w')
	file.write(HEADER + '\n')
	for i in keys:
		file.write('%s\n' % new[i])
def help():
	print """ - Setup -

	valid options:
		-h 	- shows help
		-f file	- default services.conf
		-c file	- default db.conf
		-n	- generates a new service.conf from db
		-u	- updates the db from services.conf
"""
if __name__=='__main__':
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hnuf:c:')
		opts = dict(opts)
		if '-h' in opts:
			help()
			sys.exit()
		file = opts.get('-f','services.conf')
		conf = opts.get('-c','db.conf')
		if not opts:
			help()
		elif not os.path.exists(conf):
			msg = 'cant find file: ' + conf 
			raise IOError(msg)
		if '-n' in opts:
			if os.path.exists(file):
				print 'creating backup: services.backup'
				open('services.backup','w').write(open(file).read())
			newFile(file,conf)
		elif '-u' in opts:
			if not os.path.exists(file):
					msg = 'cant find file: ' + file
					raise IOError(msg)
			else:
				print 'creating backup: services.backup'
				open('services.backup','w').write(open(file).read())
			main(file,conf)
		sys.exit(0)
	except (getopt.error):
		pass
	sys.exit(2)

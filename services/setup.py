"""
$Id: setup.py,v 1.11 2002/08/08 18:09:33 magnun Exp $
"""
import os
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
os.sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/handler")
import re,getopt,sys,config,database,psycopg,jobmap,string,db

HEADER = '#sysname              handler    args'

mapper = jobmap.jobmap()

class Service:
	def __init__(self, sysname, handler, args, id=''):
		self.sysname = sysname
		self.handler = handler
		self.args = args
		self.id = id
		self.active='t'
	def __cmp__(self, obj):
		return self.sysname==obj.sysname and self.handler==obj.handler and self.args==obj.args
	def __eq__(self, obj):
		return self.sysname==obj.sysname and self.handler==obj.handler and self.args==obj.args
	def __hash__(self):
		value = self.sysname.__hash__() + self.handler.__hash__() + self.args.__str__().__hash__()
		value = value % 2**31
		return int(value)
	def __repr__(self):
		strargs = string.join(map(lambda x: x+'='+self.args[x], self.args))
		return "%-20s %-10s %s" % (self.sysname, self.handler, strargs)

def parseLine(line):
	line = line.strip()
	w = line.split()
	sysname = w[0]
	handler = w[1]
	args = w[2:]
	try:
		args=dict(map(lambda x: tuple(x.split('=')), args))
	except ValueError:
		print "Argumentet har ikke riktig syntax: %s" % args
		args=""
	
	if handler not in mapper:
		msg = "no such handler/type: (%s)" % handler
		raise TypeError(msg)

	#Handle boxless services
	if sysname == 'none':
		sysname = ""

	return Service(sysname, handler, args)

def fromFile(file):
	new = []
	for i in open(file).read().split('\n'):
		i = i.split('#')[0]
		if i:
			service = parseLine(i)
			new += [service]
	return new

## class DB:
## 	def __init__(self,conf):
## 		self.conf = conf
## 	def connect(self):
## 		conf = self.conf
## 		self.db = psycopg.connect("host = %s user = %s dbname = %s password = %s" % (conf["dbhost"],"manage",conf["db_nav"],conf["userpw_manage"]))
## 		self.db.autocommit(1)
## 		self.sysboks()
## 		database.db = self.db
## 	def sysboks(self):
## 		s = self.query('select sysname,boksid from boks')
## 		self.boks = dict(s)
## 	def query(self,querystring):
## 		s = self.db.cursor()
## 		s.execute(querystring)
## 		return s.fetchall()
## 	def fromDB(self):
## 		services = []

## 		for i in database.getJobs(0):
## 			serviceid = i.getServiceid()
## 			active = (i.active and 'true') or 'false'
## 			boksid = i.getBoksid()
## 			for j in self.boks:
## 				if self.boks[j] == boksid:
## 					sysname = j
## 					break
## 			handler = i.getType()
## 			args = i.getArgs()
			
## 			new = Service(sysname, handler, args, serviceid)
## 			services += [new]
## 		services.sort()
## 		return services

## 	def delete(self,service):
## 		print "serviceid: %s" % service
## 		s = self.db.cursor()
## 		s.execute("DELETE FROM service WHERE serviceid = '%s'" % service.id)

## 	def insertservice(self,service):
## 		s = self.db.cursor()
## 		next = self.query("select nextval('service_serviceid_seq')")[0][0]
## 		s.execute("INSERT INTO service (serviceid,boksid,handler) VALUES (%s,%s,'%s')" % (next, self.boks[service.sysname], service.handler))
## 		service.id = next
## 		self.insertargs(service)

## 	def insertargs(self,service):
## 		s = self.db.cursor()
## 		s.execute('DELETE FROM serviceproperty WHERE serviceid = %s' % service.id)
## 		for prop,value in service.args.items():
## 			s.execute("INSERT INTO serviceproperty (serviceid,property,value) values (%s,'%s','%s')" % (service.id,prop,value))

def newFile(file,conf):
	conf = config.config(conf)
	#db = DB(conf)
	#db.connect()
	database=db.db(conf)

	print 'fetching services from db'
	services = database.getServices()

	print 'creating ' + file
	file = open(file,'w')
	file.write(HEADER + '\n')
	for i in services:
		file.write('%s\n' % i)
	
		
def main(file,conf):
	conf = config.config(conf)
	#db = DB(conf)
	database = db.db(conf)

	print 'parsing file'
	fileEntries = fromFile(file)
	print "Entries in file: %i" % len(fileEntries)
	
	#db.connect()
	dbEntries = database.getServices()
	print "Entries in db: %i" % len(dbEntries)

	delete = filter(lambda x: x not in fileEntries, dbEntries)
	new = filter(lambda x: x not in dbEntries, fileEntries)

	if delete:
		print "Elements to be deleted: %i" % len(delete)
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
			database.deleteService(i)
	print 'updating db'

	print "Elements to add: %i" % len(new)
	for each in new:
		print "Adding service: %s" % each
		database.insertService(each)

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

#!/usr/bin/env python
"""
$Id: Timeout.py,v 1.1 2002/06/28 13:46:11 erikgors Exp $
"""
import getopt,signal,os,sys

if __name__ == '__main__':
	opts,args = getopt.getopt(sys.argv[1:],'t:')
	opts = dict(opts)
	timeout = opts.get('-t',0)
	signal.alarm( int(timeout) )
#	os.system(' '.join(args))
	f = os.popen(' '.join(args))
	print f.read()

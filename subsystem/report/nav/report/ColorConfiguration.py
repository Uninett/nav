from re import search

class ColorConfiguration:

	def __init__(self,path):
		config = file(path).readlines()
		limits = {}
		extras = {}
		for line in config:
			limitmatch = search("^\s*\>\=?\s*(\d+)\s*:\s*(\S+)",line)
			if limitmatch:
				limits[limitmatch.group(1)] = limitmatch.group(2)
			else:
				wordmatch = search("^\s*(\w+)\s*:\s*(\S+)",line)
				if wordmatch:
					extras[wordmatch.group(1)] = wordmatch.group(2)

		self.extras = extras
		self.limits = limits

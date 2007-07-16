def sub(a,b):
	return a-b

def contains(list, element):
	try:
		list.index(element)
		return True
	except ValueError:
		return False

import math
factors = {
     # f   short  long
     -24: ('y', 'yocto'),
     -21: ('z', 'zepto'),
     -18: ('a', 'atto'),
     -15: ('f', 'femto'),
     -12: ('p', 'pico'),
     -9 : ('n', 'nano'),
     -6 : ('&micro;', 'micro'),
     -3 : ('m', 'milli'),
      0 : ('', ''),
      3 : ('k', 'kilo'),
      6 : ('M', 'mega'),
      9 : ('G', 'giga'),
     12 : ('T', 'terra'),
     15 : ('P', 'peta'),
     18 : ('E', 'exa'),
     21 : ('Z', 'zetta'),
     24 : ('Y', 'yotta'),
 }
     
def sci(foo, long=False):
    foo = float(foo)
    try:
        exp = int(math.log10(foo) / 3)*3
        if abs(exp) > 24:
          exp = 24 * (exp/abs(exp))
        bar = foo / 10**exp
        # note - long means column 1, short is col 0 =)
        ret = (bar,factors[exp][long])        
    except OverflowError:
        ret = (0,'')
    return ret

def sciShort(foo):
    return sci(foo, long=False)
    
def sciLong(foo):
    return sci(foo, long=True)
    
def printe(f):
    import sci_exp
    a = sci_exp.sciShort(f)
    return '%0.3f%s' % a


        
    

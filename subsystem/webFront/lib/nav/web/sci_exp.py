import math
units = {
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
     
def sci(number, long=False):
    number = float(number)
    try:
        exponent = int(math.log10(number) / 3)*3
        if abs(exponent) > 24:
          exponent = 24 * (exponent/abs(exponent))
        factor = number / 10**exponent
        # note - long means column 1, short is col 0 =)
        return (factor,units[exponent][long])        
    except OverflowError:
        return (0,'')

def sciShort(number):
    return sci(number, long=False)
    
def sciLong(number):
    return sci(number, long=True)
    
def printe(number):
    import sci_exp
    a = sci_exp.sciShort(number)
    return '%0.3f%s' % a


        
    

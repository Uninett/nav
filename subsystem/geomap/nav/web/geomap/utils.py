#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""General utility functions for Geomap.

This file contains functions which I wish were in the standard
library.

"""


def group(property, lst):
    """Group a list into sublists based on equality of some property.

    Returns a list of sublists of lst, where every item of lst appears
    in exactly one sublist, and two items are in the same sublist iff
    the result of applying property (a function) to either of them
    gives the same result.

    """
    hash = {}
    for x in lst:
        p = property(x)
        if p in hash:
            hash[p].append(x)
        else:
            hash[p] = [x]
    return hash.values()


def avg(lst):
    """Return the average of the values in lst.  lst should be a list
    of numbers.

    """
    if len(lst) == 0:
        return 0
    return float(sum(lst))/len(lst)


def weighted_avg(lst):
    if len(lst) == 0:
        return 0
    total = sum(map(lambda (value,weight): value*weight, lst))
    num = sum(map(lambda (value,weight): weight, lst))
    return float(total)/num


def fix(fun, argvalues, argnums=0):
    if not isinstance(argvalues, list):
        argvalues = [argvalues]
    def derived(*args, **kwargs):
        args = list(args)
        if isinstance(argnums, int):
            args[argnums:argnums] = argvalues
        else:
            for i in xrange(len(argnums)):
                args.insert(argnums[i], argvalues[i])
        return apply(fun, args, kwargs)
    return derived


def numeric(obj):
    return isinstance(obj, int) or isinstance(obj, float)


def float_or_nan(string):
    try:
        return float(string)
    except ValueError:
        return float('nan')


def compose(*functions):
    return reduce(lambda f1, f2: lambda x: f1(f2(x)),
                  functions)


def subdict(d, keys):
    """Restriction of dictionary to some keys.

    d should be a dictionary and keys a list whose items are keys of
    d.  Returns a new dictionary object.

    """
    return dict([(k, d[k]) for k in keys])


def filter_dict(fun, d):
    """Filter a dictionary on values.

    Like the built-in filter, except that d is a dictionary, and fun
    is applied to each value. The result is a new dictionary
    containing those (key,value) pairs from d for which fun(value) is
    true.

    """
    return subdict(d, filter(lambda key: fun(d[key]), d))


def map_dict(fun, d):
    """Map over a dictionary's values.

    Returns a new dictionary which is like d except that each value is
    replaced by the result of applying fun to it.

    """
    return dict(map(lambda (key, value): (key, fun(value)),
                    d.items()))


def union_dict(*dicts):
    """Combine dictionaries.

    Combines all arguments (which should be dictionaries) to a single
    dictionary. If several dictionaries contain the same key, the last
    is used.

    """
    lazy_p = any(map(lambda d: isinstance(d, lazy_dict), dicts))
    if lazy_p:
        result = lazy_dict()
    else:
        result = {}
    for d in dicts:
        result.update(d)
    return result


def concat_list(lists):
    """Concatenate a list of lists."""
    return reduce(lambda a,b: a+b, lists, [])


def concat_str(strs):
    """Concatenate a list of strings."""
    return reduce(lambda a,b: a+b, strs, '')


class lazy_dict(dict):
    unevaluated = None

    def __init__(self, *args, **kwargs):
        super(lazy_dict, self).__init__(*args, **kwargs)
        self.unevaluated = set([])

    def __getitem__(self, key):
        if isinstance(key, list):
            real_key = key[0]
            val = super(lazy_dict, self).__getitem__(real_key)
            if real_key in self.unevaluated:
                return val
            else:
                return {'value': val}
        else:
            return self.force_and_call(key, '__getitem__', key)

    def copy(self):
        cp = lazy_dict()
        for key in self.keys():
            cp[[key]] = self[[key]]
        return cp

    def get(self, key, default=None):
        return self.force_and_call(key, 'get', key, default)

    def items(self):
        return self.force_and_call(None, 'items')

    def iteritems(self):
        return self.force_and_call(None, 'iteritems')

    def itervalues(self):
        return self.force_and_call(None, 'itervalues')

    def pop(self, key, *args):
        if key in self:
            self.force(key)
        return super(lazy_dict, self).pop(key, *args)

    def popitem(self):
        if len(self.keys()) == 0:
            raise KeyError('dictionary is empty')
        key = self.keys()[0]
        val = self.pop(key)
        return (key,val)

    #TODO: setdefault

    def update(self, d1, **d2):
        if isinstance(d1, lazy_dict):
            for key in d1.keys():
                self[[key]] = d1[[key]]
        else:
            super(lazy_dict, self).update(d1)
        if len(d2.keys()) > 0:
            self.update(d2)

    def values(self):
        return self.force_and_call(None, 'values')

    def __setitem__(self, key, val):
        if isinstance(key, list):
            real_key = key[0]
            if isinstance(val, dict):
                if val.has_key('value'):
                    val = val['value']
                else:
                    self.unevaluated.add(real_key)
                super(lazy_dict, self).__setitem__(real_key, val)
            else:
                if isinstance(val, tuple):
                    fun = val[0]
                    args = val[1:]
                else:
                    fun = val
                    args = []
                self.set_lazy(real_key, fun, *args)
        else:
            super(lazy_dict, self).__setitem__(key, val)

    def set_lazy(self, key, fun, *args):
        super(lazy_dict, self).__setitem__(key, {'fun': fun, 'args': args})
        self.unevaluated.add(key)

    def __repr__(self):
        return '<lazy_dict %s>' % super(lazy_dict, self).__repr__()

    def force(self, key):
        if len(self.unevaluated) == 0:
            return
        if key is None:
            self.force(self.keys())
        elif isinstance(key, list):
            for k in key:
                self.force(k)
        elif key in self.unevaluated:
            fun = super(lazy_dict, self).__getitem__(key)['fun']
            args = super(lazy_dict, self).__getitem__(key)['args']
            val = apply(fun, args)
            super(lazy_dict, self).__setitem__(key, val)
            self.unevaluated.remove(key)

    def force_and_call(self, key, method, *args):
        self.force(key)
        return type(dict).__getattribute__(dict, method)(self, *args)


def map_dict_lazy(fun, d):
    res = lazy_dict()
    for key in d:
        res.set_lazy(key, fun, d[key])
    return res


# 'any' is in the standard library from version 2.5.
# This code copied from http://docs.python.org/library/functions.html#any
def any(iterable):
    for element in iterable:
        if element:
            return True
    return False

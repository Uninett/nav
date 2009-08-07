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
    """Compute the average of the values in lst.

    Arguments:

    lst -- a list of numbers.

    """
    if len(lst) == 0:
        return 0
    return float(sum(lst))/len(lst)


def weighted_avg(lst):
    """Compute a weighted average.

    Arguments:

    lst -- a list of tuples (value, weight)

    """
    if len(lst) == 0:
        return 0
    total = sum(map(lambda (value,weight): value*weight, lst))
    num = sum(map(lambda (value,weight): weight, lst))
    return float(total)/num


def argmax(fun, lst):
    """Find an argument to fun from lst giving maximal value.

    Return value: An element m of lst with the property that for any
    element e in lst, fun(m) >= fun(e).

    Arguments:

    fun -- the single-argument function to maximize

    lst -- list of possible arguments to fun

    """
    max_item = lst[0]
    max_val = fun(lst[0])
    for x in lst[1:]:
        x_val = fun(x)
        if x_val > max_val:
            max_item = x
            max_val = x_val
    return max_item


def nansafe_max(lst):
    """Find the maximum value in lst, ignoring any NaN values.

    The builtin max function (on my system, at least) returns NaN if
    the first value is NaN and the maximum of the non-NaN values in
    all other cases; which means it gives different results for
    different permutations of a list when both NaN and other values
    are involved.

    This function returns NaN if and only if _all_ values in lst are
    NaN; otherwise it returns the largest non-NaN value.

    """
    values = filter(negate(is_nan), lst)
    if len(values) == 0:
        return float('nan')
    return max(values)


def fix(fun, argvalues, argnums=0):
    """Fix one or more arguments to a function.

    Returns a new function which is like fun, but takes len(argvalues)
    (or 1 if argvalues is not a list) fewer arguments. This function,
    when called, combines the arguments it is given with argvalues,
    passes the resulting list as arguments to fun, and returns the
    result.

    Arguments:

    fun -- base function

    argvalues -- fixed argument values. Passing a non-list value as
    argvalues is equivalent to passing a single-element list
    containing that value.

    argnums -- positions of argvalues in the argument list. Must be
    either a list of numbers with same length as argvalues or a
    number. If it is a list, it specifies the position in fun's
    argument list for each value in argvalues. If it is a single
    number, it specifies the position for the first value in
    argvalues; the remaining values are placed in the subsequent
    positions.


    """
    if not isinstance(argvalues, list):
        argvalues = [argvalues]
    def derived(*args, **kwargs):
        args = list(args)
        if isinstance(argnums, int):
            args[argnums:argnums] = argvalues
        else:
            for i in xrange(len(argnums)):
                # TODO this may put arguments in wrong places; should be fixed
                args.insert(argnums[i], argvalues[i])
        return apply(fun, args, kwargs)
    return derived


def numeric(obj):
    """Check whether an object is a number."""
    return isinstance(obj, int) or isinstance(obj, float)


def float_or_nan(string):
    """Convert a string to a float if possible, otherwise return the NaN value.
    """
    try:
        return float(string)
    except ValueError:
        return float('nan')


def is_nan(val):
    """Check if val is the special NaN (not a number) floating point value.

    This test is, apparently, somewhat platform-dependent (see [1]).
    From Python 2.6, this should be replaced by math.isnan.

    [1]: http://groups.google.com/group/comp.lang.python/browse_thread/thread/17f4cae77e28814b/eaa6a2753877737d#msg_61950ec8cae12f8f

    """
    return val != val


def compose(*functions):
    """Function composition.

    Each argument should be a single-argument function.

    The return value is a function such that the following holds for
    any x:

      compose(f_1, f_2, ..., f_n)(x) == f_1(f_2(...(f_n(x))))

    """
    return reduce(lambda f1, f2: lambda x: f1(f2(x)),
                  functions)


def negate(p):
    """Negate the predicate (i.e., boolean function) p.

    Returns a function np with the property that

      np(x_1, ..., x_n) == not p(x_1, ..., x_n)

    for all x_1, ..., x_n.

    """
    def np(*args):
        return not p(*args)
    return np


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


class lazy_dict:
    """A dictionary with values that are computed only when needed.

    This class provides a very limited form of lazy evaluation. When
    setting a value in the dictionary, the value may be given either
    directly or indirectly by a function for computing it. In the
    latter case, the function will be called (and the resulting value
    stored for later lookups) the first time the value is read from
    the dictionary.

    A lazy_dict may be used mostly as a dictionary. Values are read
    and written with the usual bracket notation (d[key]). For lazy
    values, a double bracket notation is provided. To set a lazy
    value, use

      d[[key]] = function

    or

      d[[key]] = (function, arg1, arg2, ...).

    If the same key is later looked up with single brackets, this
    function is called with these arguments (if any) and the resulting
    value returned.

    Double brackets may also be used for reading to copy a value (to
    another lazy_dict or a different key in the same dictionary)
    without evaluating it:

      d1[[key1]] = d2[[key2]].

    (The double bracket notation is not any special syntax, just a
    trick to create something which looks like it. As far as Python is
    concerned, the outermost brackets are exactly the same as in
    single bracket notation, while the inner brackets denote list
    construction. The bracket functionality is implemented by
    __getitem__ and __setitem__ (since Python automagically translates
    the expression d[k] to d.__getitem__(k) and the statement d[k]=v
    to d.__setitem__(k,v)), and these simply check whether their first
    argument is a list in order to determine whether single or double
    brackets are used. (Note that a list can not be used as a
    dictionary key, so this does not interfere with potential keys)).

    """

    unevaluated = None # set of keys whose values are not evaluated
    storage = None # dictionary for storing functions and evaluated values

    def __init__(self, *args, **kwargs):
        self.unevaluated = set([])
        self.storage = dict(*args, **kwargs)

    def __getitem__(self, key):
        """d.__getitem__(k) <==> d[k]"""
        if isinstance(key, list):
            real_key = key[0]
            val = self.storage[real_key]
            if real_key in self.unevaluated:
                return val
            else:
                return {'value': val}
        else:
            self.force(key)
            return self.storage[key]

    def __contains__(self, key):
        """d.__contains__(k) <==> k in d"""
        return self.storage.__contains__(key)

    def copy(self):
        """Returns a new lazy_dict with the same contents as this.

        Lazy (unevaluated) values are preserved as such in the
        copy. If any of these values is later looked up in either the
        original or in the copy, it will still remain unevaluated in
        the other one.

        """
        cp = lazy_dict()
        for key in self.keys():
            cp[[key]] = self[[key]]
        return cp

    def get(self, key, default=None):
        """Returns self[key] if key is a key in self, default otherwise."""
        return self.force_and_call(key, 'get', key, default)

    def keys(self):
        """Returns the dictionary's keys as a list."""
        return self.storage.keys()

    def items(self):
        """Returns all (key,value) pairs (like dict.items).

        This forces all values to be evaluated.

        """
        return self.force_and_call(None, 'items')

    def update(self, d1, **d2):
        """Add values from another dictionary and/or keyword arguments.

        If d1 is a lazy_dict, laziness is preserved for elements added
        from it.

        """
        if isinstance(d1, lazy_dict):
            for key in d1.keys():
                self[[key]] = d1[[key]]
        else:
            for key in d1.keys():
                self[key] = d1[key]
        if len(d2.keys()) > 0:
            self.update(d2)

    def values(self):
        """Returns all the dictionary's values as a list.

        This forces all values to be evaluated.

        """
        return self.force_and_call(None, 'values')

    def __setitem__(self, key, val):
        """d.__setitem__(key, val) <==> d[key] = val."""
        if isinstance(key, list):
            real_key = key[0]
            if isinstance(val, dict):
                if val.has_key('value'):
                    val = val['value']
                else:
                    self.unevaluated.add(real_key)
                self.storage[real_key] = val
            else:
                if isinstance(val, tuple):
                    fun = val[0]
                    args = val[1:]
                else:
                    fun = val
                    args = []
                self.set_lazy(real_key, fun, *args)
        else:
            self.storage[key] = val
            self.unevaluated.discard(key)

    def set_lazy(self, key, fun, *args):
        """Set a lazy value.

        Double bracket notation may be used instead of this function:
        d.set_lazy(k, f, a1, a2) is equivalent to d[[k]] = (f, a1, a2).

        """
        self.storage[key] = {'fun': fun, 'args': args}
        self.unevaluated.add(key)

    def __repr__(self):
        return '<lazy_dict %s>' % self.storage

    def force(self, key):
        """Force certain value(s) to be evaluated.

        If key is None, evaluate all values. If key is a list evaluate
        self[k] for each k in key. Otherwise, evaluate d[key].

        """
        if len(self.unevaluated) == 0:
            return
        if key is None:
            self.force(self.keys())
        elif isinstance(key, list):
            for k in key:
                self.force(k)
        elif key in self.unevaluated:
            fun = self.storage[key]['fun']
            args = self.storage[key]['args']
            val = apply(fun, args)
            self.storage[key] = val
            self.unevaluated.remove(key)

    def force_and_call(self, key, method, *args):
        """Call a method on the underlying dict after forcing evaluation of key.
        """
        self.force(key)
        return type(dict).__getattribute__(dict, method)(self.storage, *args)


def map_dict_lazy(fun, d):
    """Like map_dict, but produces a lazy_dict instead of a dict.

    Each value in the dictionary is set lazily."""
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


def first(lst):
    """Extract the first element from a list or other indexable object."""
    return lst[0]

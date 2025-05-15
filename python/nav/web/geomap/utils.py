#
# Copyright (C) 2009, 2010, 2013, 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

import math
from itertools import groupby
from functools import reduce


def identity(obj):
    """identity(obj) == obj for all obj"""
    return obj


def group(keyfunc, lst):
    """Groups a list into sublists based on equality of some keyfunc.

    Returns a list of sublists of lst, where every item of lst appears
    in exactly one sublist, and two items are in the same sublist iff
    the result of applying keyfunc (a function) to either of them
    gives the same result.

    """
    data = sorted(lst, key=keyfunc)
    return [list(grp) for _key, grp in groupby(data, keyfunc)]


def avg(lst):
    """
    Computes the average of the values in lst.

    :param lst: A list of numbers.
    :return: An average value of the list.

    """
    if not lst:
        return 0
    return float(sum(lst)) / len(lst)


def weighted_avg(lst):
    """
    Computes a weighted average.

    :param lst: a list of tuples (value, weight)
    :return: A weighted average.

    """
    if not lst:
        return 0
    total = sum(value * weight for value, weight in lst)
    num = sum(weight for value, weight in lst)
    return float(total) / num


def argmax(fun, lst):
    """
    Finds the element of lst with the maximum fun(lst) value.

    :param fun: The single-argument function to maximize
    :param lst: List of values.
    :return: The element of lst with the maximum fun(lst) value.

    """
    return sorted(lst, key=fun)[-1]


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
    try:
        return max(v for v in lst if not is_nan(v))
    except ValueError:
        return float('nan')


def numeric(obj):
    """Check whether an object is a number."""
    return isinstance(obj, int) or isinstance(obj, float)


def float_or_nan(string):
    """Convert a string to a float if possible, otherwise return the NaN value."""
    try:
        return float(string)
    except ValueError:
        return float('nan')


def is_nan(val):
    """Verifies whether val is the special NaN floating point value."""
    try:
        return math.isnan(val)
    except TypeError:
        return False


def compose(*functions):
    """Function composition.

    Each argument should be a single-argument function.

    The return value is a function such that the following holds for
    any x:

      compose(f_1, f_2, ..., f_n)(x) == f_1(f_2(...(f_n(x))))

    """
    return reduce(lambda f1, f2: lambda x: f1(f2(x)), functions)


def subdict(dct, keys):
    """Restriction of dictionary to some keys.

    dct should be a dictionary (or lazy_dict) and keys a list whose
    items are keys of dct.  Returns a new dictionary object; dct is not
    modified.  If dct is a lazy_dict, the result is also a lazy_dict.

    """
    if isinstance(dct, lazy_dict):
        newdct = dct.copy()
        for k in dct.keys():
            if k not in keys:
                del newdct[k]
        return newdct
    else:
        return {k: dct[k] for k in keys}


def filter_dict(fun, dct):
    """Filter a dictionary on values.

    Like the built-in filter, except that dct is a dictionary, and fun
    is applied to each value. The result is a new dictionary
    containing those (key,value) pairs from dct for which fun(value) is
    true.

    """
    return subdict(dct, [key for key, val in dct.items() if fun(val)])


def map_dict(fun, dct):
    """Map over a dictionary's values.

    Returns a new dictionary which is like dct except that each value is
    replaced by the result of applying fun to it.

    """
    return {k: fun(v) for k, v in dct.items()}


def union_dict(*dicts):
    """Combine dictionaries.

    Combines all arguments (which should be dictionaries) to a single
    dictionary. If several dictionaries contain the same key, the last
    is used.

    """
    lazy_p = any(isinstance(d, lazy_dict) for d in dicts)
    if lazy_p:
        result = lazy_dict()
    else:
        result = {}
    for dct in dicts:
        result.update(dct)
    return result


def concat_list(lists):
    """Concatenate a list of lists."""
    return reduce(lambda a, b: a + b, lists, [])


def concat_str(strs):
    """Concatenate a list of strings."""
    return reduce(lambda a, b: a + b, strs, '')


class lazy_dict(object):
    """A dictionary with values that are computed only when needed.

    This class provides a very limited form of lazy evaluation. When
    setting a value in the dictionary, the value may be given either
    directly as when using an ordinary dictionary, or indirectly by a
    function for computing it. In the latter case, the function will
    be called (and the resulting value stored for later lookups) the
    first time the value is read from the dictionary.

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

    unevaluated = None  # set of keys whose values are not evaluated
    storage = None  # dictionary for storing functions and evaluated values

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
        cpy = lazy_dict()
        for key in self.keys():
            cpy[[key]] = self[[key]]
        return cpy

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

    def update(self, dict1, **dict2):
        """Add values from another dictionary and/or keyword arguments.

        If dict1 is a lazy_dict, laziness is preserved for elements added
        from it.

        """
        if isinstance(dict1, lazy_dict):
            for key in dict1.keys():
                self[[key]] = dict1[[key]]
        else:
            for key in dict1.keys():
                self[key] = dict1[key]
        if dict2:
            self.update(dict2)

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
                if 'value' in val:
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

    def __delitem__(self, key):
        """d.__delitem__(key) <==> del d[key]."""
        del self.storage[key]
        self.unevaluated.discard(key)

    def remove_if_present(self, key):
        """Remove key key from dictionary if it is present."""
        if key in self:
            del self[key]

    def swap(self, key1, key2):
        """Swap the values at keys key1 and key2."""
        self[[key1]], self[[key2]] = self[[key2]], self[[key1]]

    def __repr__(self):
        return '<lazy_dict %s>' % self.storage

    def force(self, key):
        """Force certain value(s) to be evaluated.

        If key is None, evaluate all values. If key is a list evaluate
        self[k] for each k in key. Otherwise, evaluate d[key].

        """
        if not self.unevaluated:
            return
        if key is None:
            self.force(self.keys())
        elif isinstance(key, list):
            for k in key:
                self.force(k)
        elif key in self.unevaluated:
            fun = self.storage[key]['fun']
            args = self.storage[key]['args']
            val = fun(*args)
            self.storage[key] = val
            self.unevaluated.remove(key)

    def force_and_call(self, key, method, *args):
        """Call a method on the underlying dict after forcing evaluation of key."""
        self.force(key)
        return type(dict).__getattribute__(dict, method)(self.storage, *args)


def map_dict_lazy(fun, dct):
    """Like map_dict, but produces a lazy_dict instead of a dict.

    Each value in the dictionary is set lazily."""
    res = lazy_dict()
    for key in dct:
        res.set_lazy(key, fun, dct[key])
    return res


def first(lst):
    """Extract the first element from a list or other indexable object."""
    return lst[0]

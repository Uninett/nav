/*
 * Copyright (C) 2009, 2010 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 3 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * util.js: Utility functions.
 */

function zip() {
    var result = [];
    var length = reduce(arguments[0].length, min, map(len, arguments));
    for (var i = 0; i < length; i++) {
	result[i] = [];
	for (var j = 0; j < arguments.length; j++)
	    result[i][j] = arguments[j][i];
    }
    return result;
}

function subarray(arr, start, end) {
    var result = [];
    if (!end)
	end = arr.length;
    for (var i = start; i < end; i++)
	result.push(arr[i]);
    return result;
}

function map(fun) {
    var i, j;
    var lists = subarray(arguments, 1);
    var result = [];
    var length = lists[0].length;
    for (j = 1; j < lists.length; j++)
	if (lists[j].length < length)
	    length = lists[j].length;
    for (var i = 0; i < length; i++) {
	var args = [];
	for (var j = 0; j < lists.length; j++)
	    args[j] = lists[j][i];
	result[i] = fun.apply(null, args);
    }
    return result;
    /*
    var res = [];
    var i;
    for (i = 0; i < list.length; i++)
	res[i] = fun(list[i]);
    return res;
    */
}

/*
 * Call the same method on each object in a list, returning the
 * results as a list. Any arguments to this function beyond the first
 * two are passed as arguments in each method call.
 */
function mapMethod(methodName, objects) {
    var args = copyArray(arguments);
    args.splice(0, 2);
    return map(function (obj) { return obj[methodName].apply(obj, args); },
	       objects);
}

function funmap(functions, arg) {
    return map(function(f) { return f(arg) }, functions);
}

function filter(pred, list) {
    var res = [];
    var i;
    for (i = 0; i < list.length; i++)
	if (pred(list[i]))
	    res.push(list[i]);
    return res;
}

function firstWith(pred, list, defaultValue) {
    var i;
    for (i = 0; i < list.length; i++)
	if (pred(list[i]))
	    return list[i];
    return defaultValue;
}

function reduce(init, fun, list) {
    var res = init;
    var i;
    for (i = 0; i < list.length; i++)
	res = fun(res, list[i]);
    return res;
}

function concat(strlist) {
    return reduce('', function(a,b) {return a+b}, strlist);
}



function encapsulate(obj, fun) {
    return function() {
	return fun.apply(obj, arguments);
    };
}


function min(a, b) {
    return (a<b) ? a : b;
}

function max(a, b) {
    return (a>b) ? a : b;
}


function member(elem, arr) {
    for (var i = 0; i < arr.length; i++) {
	if (arr[i] == elem)
	    return true;
    }
    return false;
}


function copyObject(obj) {
    var cp = {};
    for (var i in obj) {
	cp[i] = obj[i];
    }
    return cp;
}

function copyArray(a) {
    var cp = [];
    for (var i = 0; i < a.length; i++)
	cp[i] = a[i];
    return cp;
}

function extend(obj, ext) {
    var res = copyObject(obj);
    for (var i in ext)
	res[i] = ext[i];
    return res;
}


function square(n) {
    return n*n;
}



function union(a, b) {
    var i;
    var u = [];
    for (i = 0; i < a.length; i++)
	u.push(a[i]);
    for (i = 0; i < b.length; i++)
	if (!member(b[i], u))
	    u.push(b[i]);
    return u;
}

function difference(a, b) {
    var i;
    var d = [];
    for (i = 0; i < a.length; i++)
	if (!member(a[i], b))
	    d.push(a[i]);
    return d;
}



function format(fstr) {
    //var re = /%([0-9]?)([dfs])/g;
    var re = new RegExp("%((.?)([0-9]))?([dfs])", 'g');
    var i;
    var lastpos = 0;
    var result = '';

    for (i = 1; i < arguments.length; i++) {
	var arr = re.exec(fstr);
	if (arr == null)
	    throw 'format -- error: too many arguments for format string "' +
	    fstr + '"';
	result += fstr.substring(lastpos, arr.index);
	result += format_value(arguments[i], arr[4], arr[3], arr[2]);
	lastpos = re.lastIndex;
    }

    result += fstr.substring(lastpos);
    return result;
}

function format_value(val, type, len, variant) {
    var str;
    var fill_char = ' ';
    switch (type) {
    case 'f':
	return val.toPrecision(len);
    case 'd':
	str = String(Math.round(val));
	if (variant == '0')
	    fill_char = '0';
	while (str.length < len)
	    str = fill_char + str;
	return str;
    case 's':
	if (len) {
	    str = val.substring(0, len);
	    while (str.length < len)
		str += fill_char;
	    return str;
	} else {
	    return val;
	}
    default:
	throw 'format -- error: invalid conversion type "'+type+'"';
    }
}




function arrayConcat(arrays) {
    return [].concat.apply([], arrays);
}



function values(obj) {
    var arr = [];
    for (var i in obj)
	arr.push(obj[i]);
    return arr;
}


function makeObject() {
    var obj = {};
    for (var i = 1; i < arguments.length; i += 2)
	obj[arguments[i-1]] = arguments[i];
    return obj;
}



function callMethod(obj, method) {
    var args = copyArray(arguments);
    args.splice(0, 2);
    return obj[method].apply(obj, args);
}

function encapsulateMethod(obj, method) {
    return encapsulate(obj, obj[method]);
}


function identity(x) {
    return x;
}

function compose() {
    return reduce(identity,
		  function(f,g) { return function(x) { return f(g(x)); }},
		  arguments);
}

function fix(fun, argvalues, positions) {
    if (!(argvalues instanceof Array))
	argvalues = [argvalues];
    if (!positions)
	positions = 0;
    function derived() {
	args = copyArray(arguments);
	if (typeof positions == 'number') {
	    args.splice.apply(args, [positions, 0].concat(argvalues));
	} else {
	    for (var i = 0; i < argvalues.length; i++) {
		args.splice(positions[i], 0, argvalues[i]);
	    }
	}
	return fun.apply(this, args);
    }
    return derived;
}


function first(x) { return x[0]; }
function second(x) { return x[1]; }
function nth(n, x) { return x[n]; }

function len(lst) { return lst.length; }

function interleave() {
    var result = [];
    var maxlen = reduce(0, max, map(len, arguments));
    for (var i = 0; i < maxlen; i++)
	for (var j = 0; j < arguments.length; j++)
	    if (i < arguments[j].length)
		result.push(arguments[j][i]);
    return result;
}

function getAllMatches(re, str) {
    var globalRE = new RegExp((re instanceof RegExp) ? re.source : re,
			      'g');
    var matches = [];
    var match;
    while (match = globalRE.exec(str))
	matches.push(match[0]);
    return matches;
}

/*
 * Replace each substring m of str matching re with the result of
 * calling fun(m).
 */
function regexpReplace(str, re, fun) {
    var around = str.split(re);
    var matches = getAllMatches(re, str);
    var replacements = map(fun, matches);
    return concat(interleave(around, replacements));
}

function range(start, end, step) {
    if (!step)
	step = 1;
    if (!end) {
	end = start;
	start = 0;
    }
    var endtest = ((step > 0) ?
		   function(i) { return i < end; } :
		   function(i) { return i > end; });
    var result = [];
    for (var i = start; endtest(i); i += step)
	result.push(i);
    return result;
}


function makeHook() {
    return [];
}

function addHook(hook, func) {
    hook.push(func);
}

function callHook(hook) {
    var args = subarray(arguments, 1);
    hook.forEach(function (f) { f.apply(null, args); });
}

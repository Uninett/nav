/*
 * Copyright (C) 2009 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
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

function map(fun, list) {
    var res = [];
    var i;
    for (i = 0; i < list.length; i++)
	res[i] = fun(list[i]);
    return res;
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

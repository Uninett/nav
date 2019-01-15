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
 * Time.js: Provides the Time type, used for representation of times
 * and time offsets.
 */


const TIME_UNITS = ['year', 'month', 'week', 'day', 'hour', 'minute'];

/*
 * Time: Representation of a time or time offset.
 *
 * This duplicates some of the functionality of the builtin Date type,
 * but adds certain things we need here.
 *
 * The major difference between Date and Time is that Time may
 * represent either an absolute point in time (such as 2009-04-01
 * 13:37) or a time offset/duration (such as three years, one month
 * and forty-two minutes). Which of these a given Time object
 * represents is not indicated in the object itself, but certain
 * operations make sense only for one of the two (it is assumed that
 * the user of Time objects is able to avoid the meaningless
 * combinations). The only nonobvious case of this is the add method,
 * which must be called on an absolute time and with an offset as
 * argument. Properties such as week (which is the week number within
 * the year), weekDay and monthName obviously do not make sense for
 * time offsets.
 *
 * Some minor differences from Date: there is a method to get the week
 * number, months are numbered starting from 1, weeks start on
 * Mondays.
 *
 * Arguments to the constructor:
 *
 * obj -- an object whose properties are copied into this object. In
 *        addition to the Time properties year, month, day, hour,
 *        minute; week is understood as shorthand for seven days.
 *
 * absolute -- boolean telling whether the Time object should
 *             represent an absolute time. The only effect of setting
 *             this is that the month and day properties are set to 1
 *             instead of 0 if not specified otherwise.
 *
 * If obj is null or omitted, a Time object representing the current
 * time is created.
 */
function Time(obj, absolute) {
    if (obj) {
	if (typeof obj == 'string') {
	    this.read(obj);
	} else {
	    if (absolute) {
		this.month = 1;
		this.day = 1;
	    }
	    this.copyPropertiesFrom(obj);
	}
    } else {
	this.year = new Date().getFullYear();
	this.month = new Date().getMonth()+1;
	this.day = new Date().getDate();
	this.hour = new Date().getHours();
	this.minute = new Date().getMinutes();
    }
}

Time.prototype = {
    year: 0,
    month: 0,
    day: 0,
    hour: 0,
    minute: 0,

    get weekDay() {
	var d = new Date(this.year, this.month-1, this.day).getDay();
	return (d + 6) % 7;
    },

    get weekDayName() {
	return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
		'Saturday', 'Sunday'][this.weekDay];
    },

    get shortWeekDayName() {
	return ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][this.weekDay];
    },

    /*
     * ISO 8601 week number (week 1 is the week containing the first
     * Thursday of a year).
     */
    get week() {
	var t = this.weekCenter();
	var startYear = t.year;
	var num = 0;
	while (t.year == startYear) {
	    t = t.add({week: -1});
	    num++;
	}
	return num;
    },

    get weekYear() {
	return this.weekCenter().year;
    },

    get monthName() {
	return ['January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October',
		'November', 'December'][this.month-1];
    },

    get shortMonthName() {
	return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
		'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][this.month-1];
    },

    /*
     * The number of days in the month of this object.
     */
    get daysInMonth() {
	if (this.month == 2) {
	    if (this.leapYear)
		return 29;
	    else
		return 28;
	} else if ((this.month <= 7 && this.month % 2 == 1) ||
		   (this.month >= 8 && this.month % 2 == 0)) {
	    return 31;
	} else {
	    return 30;
	}
    },

    /*
     * true if the year of this object is a leap year, false
     * otherwise.
     */
    get leapYear() {
	return ((this.year % 400 == 0) ||
		((this.year % 4 == 0) && (this.year % 100 != 0)));
    },

    /*
     * Returns a Time object representing the Thursday in the same
     * week as this object.
     */
    weekCenter: function() {
	return this.add({day: 3-this.weekDay});
    },

    compare: function(t) {
	for (var i = 0; i < TIME_UNITS.length; i++) {
	    var unit = TIME_UNITS[i];
	    if (unit == 'week') continue;
	    if (this[unit] < t[unit])
		return -1;
	    if (this[unit] > t[unit])
		return 1;
	}
	return 0;
    },

    /*
     * Add a time offset to this time, returning the sum (this object
     * is not modified).
     *
     * offset should be either a Time object or an appropriate object
     * for passing to the Time constructor.
     *
     * It is assumed that the object add is called on represents an
     * absolute time, while the argument represents a time offset.
     */
    add: function(offset) {

	// adjust: Helper function (probably easier to understand by
	// looking at calls below than at this explanation). Adjust
	// (by destructively modifying) obj such that its small
	// property is in the interval [minval,minval+size] by
	// overflowing anything beyond this into the large property,
	// assuming that there are size small's for each large.
	function adjust(obj, large, small, size, minval) {
	    if (obj[small] < minval) {
		obj[large] -= Math.ceil((minval-obj[small]) / size);
		obj[small] = size + minval - (minval-obj[small]) % size;
	    } else if (obj[small] >= size + minval) {
		obj[large] += Math.floor((minval+obj[small]) / size);
		obj[small] = (minval+obj[small]) % size - minval;
	    }
	}

	if (!(offset instanceof Time))
	    offset = new Time(offset);

	var sum = new Time({year: this.year + offset.year,
			    month: this.month + offset.month,
			    day: this.day,
			    hour: this.hour + offset.hour,
			    minute: this.minute + offset.minute});
	adjust(sum, 'year', 'month', 12, 1);
	if (sum.day > sum.daysInMonth)
	    sum.day = sum.daysInMonth;
	sum.day += offset.day;
	adjust(sum, 'hour', 'minute', 60, 0);
	adjust(sum, 'day', 'hour', 24, 0);
	while (sum.day < 1) {
	    sum.month--;
	    adjust(sum, 'year', 'month', 12, 1);
	    sum.day += sum.daysInMonth;
	}
	while (sum.day > sum.daysInMonth) {
	    sum.day -= sum.daysInMonth;
	    sum.month++;
	    adjust(sum, 'year', 'month', 12, 1);
	}

	return sum;
    },

    relative: function(t) {
	var newTime = new Time(this);
	newTime.copyPropertiesFrom(t);
	return newTime;
    },

    copyPropertiesFrom: function(t) {
	for (var i in t)
	    if (member(i, ['year', 'month', 'day', 'hour', 'minute']))
		this[i] = t[i];
	if (t.week && !(t instanceof Time))
	    this.day += t.week*7;
    },

    /*
     * Returns a Date object representing the same time as this.
     */
    toDate: function() {
	return new Date(this.year, this.month-1, this.day,
			this.hour, this.minute);
    },

    /*
     * Format this date according to a format string, in which any
     * two-character sequence starting with '%' is magic. The format
     * characters that may be used are a subset of those understood by
     * date(1).
     */
    format: function(fstr) {

	// fcharDefs: Table of format characters, mapping each format
	// character to a list containing the name of the property to
	// look up for replacing that format character, and a format
	// string for formatting the value:
	var fcharDefs = {
	    'A': ['weekDayName', '%s'],
	    'a': ['shortWeekDayName', '%s'],
	    'B': ['monthName', '%s'],
	    'b': ['shortMonthName', '%s'],
	    'd': ['day', '%02d'],
	    'G': ['weekYear', '%04d'],
	    'H': ['hour', '%02d'],
	    'm': ['month', '%02d'],
	    'M': ['minute', '%02d'],
	    'V': ['week', '%02d'],
	    'Y': ['year', '%04d']
	};

	// expand: Helper function which returns the replacement
	// string for a format sequence where the format character is
	// fchar.
	var expand = encapsulate(this, function(fchar) {
	    if (fchar == '%')
		return '%';
	    var def = fcharDefs[fchar];
	    if (def)
		return format(def[1], this[def[0]]);
	    return format('[unknown format character \'%s\']', fchar);
	});
	
	return regexpReplace(fstr, /%./, compose(expand, second));
    },

    /*
     * Alternative implementation of format, using the toLocaleFormat
     * method of the builtin Date type.
     *
     * This has the advantage that more format characters are
     * recognized, but the following disadvantages:
     *
     * -- Date.toLocaleFormat is non-standard (see
     *    https://developer.mozilla.org/en/Core_JavaScript_1.5_Reference/Global_Objects/Date/toLocaleFormat)
     *
     * -- Date.toLocaleFormat seems to mess up UTF-8 contents of the
     *    format string, at least in my Firefox.
     */
    format_: function(fstr) {
	return this.toDate().toLocaleFormat(fstr);
    },

    toReadableString: function() {
	return this.format('%Y%m%d%H%M');
    },

    read: function(str) {
	m = /(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/.exec(str);
	if (!m)
	    throw new Error(format('Time.read -- not a valid time string: "%s"',
				   str));
	this.year = Number(m[1]);
	this.month = Number(m[2]);
	this.day = Number(m[3]);
	this.hour = Number(m[4]);
	this.minute = Number(m[5]);
    },

    toString: function() {
	return this.format('%Y-%m-%d %H:%M');
    }
};


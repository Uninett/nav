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
 * TimeInterval.js: Provides the TimeInterval type, which represents
 * time interval in certain fixed sizes and has methods for navigating
 * between such intervals.
 */


/*
 * The sizes of the intervals we operate with. Each size is specified
 * as a certain number (n) of a certain time unit.
 *
 * Two format strings are supplied for each size: format specifies how
 * an interval should be displayed by itself, while shortFormat is
 * intended for displaying several intervals in the context of one of
 * a larger size (in practice: in the drop-down menu used for
 * selecting a smaller interval).
 *
 * If format is a list of two strings, they are used for formatting
 * the start and end time, respectively, and the results are
 * concatenated together.
 */
const TI_SIZES = [
    {n: 1, unit: 'year', format: '%Y'},
    {n: 1, unit: 'month', format: '%Y-%m', shortFormat: '%m'},
    {n: 1, unit: 'week', format: '%Y, week %V', shortFormat: '%V'},
    {n: 1, unit: 'day', format: '%Y-%m-%d', shortFormat: '%m-%d: %a'},
    {n: 1, unit: 'hour', format: ['%Y-%m-%d %H:00','–%H:00'], shortFormat: '%H'},
    {n: 10, unit: 'minute', format: ['%Y-%m-%d %H:%M','–%H:%M'], shortFormat: '%M'}
];

/*
 * Symbolic names for indices into TI_SIZES.
 */
const TI_YEAR = 0;
const TI_MONTH = 1;
const TI_WEEK = 2;
const TI_DAY = 3;
const TI_HOUR = 4;
const TI_10MIN = 5;
const TI_5MIN = 5;

/*
 * Gives a nice, displayable name for an interval size (an element of
 * TI_SIZES). If omitNIfOne is true, the number part of the size is
 * omitted if it is 1.
 *
 * Examples:
 *  sizeName(TI_SIZES[TI_YEAR])        => '1 year'
 *  sizeName(TI_SIZES[TI_YEAR], true)  => 'year'
 *  sizeName(TI_SIZES[TI_5MIN])        => '5 minutes'
 *  sizeName(TI_SIZES[TI_5MIN], true)  => '5 minutes'
 */
function sizeName(size, omitNIfOne) {
    if (omitNIfOne && size.n == 1)
	return size.unit;
    return format('%d %s%s', size.n, size.unit, size.n==1?'':'s');
}

/*
 * Representation of a time interval of one of the fixed sizes
 * specified in TI_SIZES, with methods for navigating to related
 * intervals such as the next or previous of the same size, or one of
 * smaller or larger size around the same time.
 *
 * Constructor arguments:
 *
 * size -- interval size, index into TI_SIZES
 *
 * time -- Time object (or object suitable for passing to the Time
 *         constructor) representing some time inside the interval.
 *         This does not need to be the start time; e.g, the following
 *         create essentially equivalent objects:
 * 
 *         new TimeInterval(TI_MONTH, {year:2009, month:4, day:15})
 *         new TimeInterval(TI_MONTH, {year:2009, month:4, day:1, hour:12})
 *
 *         If omitted, time defaults to one interval size back in time
 *         from the current time, giving the last finished interval of
 *         the given size.
 */
function TimeInterval(size, time) {
    if (typeof size == 'string') {
	this.read(size);
	return;
    }

    this.size = size;
    if (time) {
	this.time = new Time(time, true);
    } else {
	// Find the last selectable interval.  By the rules in
	// TimeInterval.selectable, it must contain an interval of the
	// smallest size which was finished at least one interval size
	// ago.
	var smallestSize = TI_SIZES[TI_SIZES.length-1];
	this.time = new Time().add(makeObject(smallestSize.unit,
					      -2*smallestSize.n));
    }
    if (size == TI_WEEK) {
	this.time = this.time.weekCenter();
    }
    if (this.sizeN() != 1) {
	this.time[this.sizeUnit()] -=
	    this.time[this.sizeUnit()] % this.sizeN();
    }
}

TimeInterval.prototype = {
    /*
     * Returns interval size as integer, in multiples of this.sizeUnit().
     */
    sizeN: function() {
	return TI_SIZES[this.size].n;
    },

    /*
     * Returns the unit of the time interval.
     *
     * The value is one of TIME_UNITS from Time.js.
     */
    sizeUnit: function() {
	return TI_SIZES[this.size].unit;
    },

    /*
     * Returns the interval size (object with properties n, unit).
     */
    getSize: function() {
	return TI_SIZES[this.size];
    },

    /*
     * Returns the size which is one step larger than the size of this
     * interval.
     */
    largerSize: function() {
	return TI_SIZES[this.size-1];
    },

    /*
     * Returns the size which is one step larger than the size of this
     * interval.
     */
    smallerSize: function() {
	return TI_SIZES[this.size+1];
    },

    /*
     * Returns a Time object representing the beginning of this
     * interval.
     */
    beginning: function() {
	var t = new Time({}, true);
	for (var i = 0; i < TIME_UNITS.length; i++) {
	    var unit = TIME_UNITS[i];
	    if (unit == 'week') {
		t.day = this.time.day;
	    } else {
		t[unit] = this.time[unit];
	    }
	    if (unit == this.sizeUnit())
		break;
	}
	if (this.sizeUnit() == 'week') {
	    t = t.add({day: -3});
	}
	return t;
    },

    /*
     * Returns a Time object representing the end of this interval.
     */
    end: function() {
	return this.next().beginning();
    },

    /*
     * Predicate telling whether all of this interval is before the
     * current time.
     */
    hasBeen: function() {
	return this.end().compare(new Time()) <= 0;
    },

    /*
     * Predicate telling whether the beginning of this interval is
     * before the current time.
     */
    hasStarted: function() {
	return this.beginning().compare(new Time()) <= 0;
    },

    /*
     * Predicate telling whether this interval should be selectable.
     *
     * The rules for selectability are (these are somewhat arbitrary
     * and ad-hoc):
     *
     * * An interval of the smallest size is selectable iff it ended
     *   at least one interval size ago.
     *
     * * An interval of a larger size is selectable iff it contains at
     *   least one selectable interval.
     */
    selectable: function() {
	if (this.size == TI_SIZES.length-1)
	    return this.next().hasBeen();
	return this.next().hasBeen() || this.downChoices().length != 0;
    },

    /*
     * Returns a new interval of the same size as this but with a
     * different time.
     */
    gotoTime: function(time) {
	return new TimeInterval(this.size, time);
    },

    /*
     * Returns a new interval of the same size as this which is offset
     * num multiples of size relative to this.
     *
     * size may be either an object with properties (units, n) or an
     * index into TI_SIZES.
     */
    add: function(size, num) {
	if (typeof size == 'number')
	    size = TI_SIZES[size];
	return this.gotoTime(this.time.add(makeObject(size.unit,
						      size.n*num)));
    },

    /*
     * Returns the next interval of the same size as this.
     */
    next: function() {
	return this.add(this.size, 1);
    },

    /*
     * Predicate telling whether it should be possible to select the
     * interval returned by this.next().
     */
    nextPossible: function() {
	return this.next().selectable();
    },

    /*
     * Returns the interval of the same size as this obtained by doing
     * a 'jump' forwards in time, i.e. adding the next larger interval
     * size.
     */
    nextJump: function() {
	return this.add(this.size-1, 1);
    },

    /*
     * Predicate telling whether it should be possible to select the
     * interval returned by this.nextJump().
     */
    nextJumpPossible: function() {
	return this.nextJump().selectable();
    },

    /*
     * Returns the next interval of the same size as this.
     */
    prev: function() {
	return this.add(this.size, -1);
    },

    /*
     * Returns the interval of the same size as this obtained by doing
     * a 'jump' forwards in time, i.e. adding the next larger interval
     * size.
     */
    prevJump: function() {
	return this.add(this.size-1, -1);
    },

    /*
     * Returns the interval of one step larger size at the same time
     * as this.
     */
    up: function() {
	if (this.size == 0)
	    return null;
	return new TimeInterval(this.size-1, this.time);
    },

    /*
     * Predicate telling whether it is possible to move up from this.
     */
    upPossible: function() {
	return this.size>1;
    },

    /*
     * Returns list of possible intervals for moving down in size from
     * this.
     */
    downChoices: function() {
	if (this.size == TI_SIZES.length-1)
	    return null;
	var start = this.beginning();
	var choices = [];
	var size = TI_SIZES[this.size+1];
	for (var i = 0; i < 100*size.n; i += size.n) {
	    var choiceOffset = makeObject(size.unit, i);
	    var choiceTime = start.add(choiceOffset);
	    if (choiceTime[this.sizeUnit()] !=
		this.time[this.sizeUnit()])
		break;
	    var choice = new TimeInterval(this.size+1, choiceTime);
	    if (!choice.selectable())
		break;
	    choices.push(choice);
	}
	return choices;
    },

    /*
     * Returns last selectable interval of this size.
     */
    last: function() {
	return new TimeInterval(this.size);
    },

    /*
     * Predicate; tells whether the Time object time is contained in
     * this interval.
     */
    contains: function(time) {
	return (this.beginning().compare(time) <= 0 &&
		this.end().compare(time) > 0);
    },

    /*
     * Make a string representation of this interval which can be read
     * back with the read function.
     */
    toReadableString: function() {
	return this.size + '-' + this.beginning().toReadableString();
    },

    /*
     * Fill this object with data from a string as produced by
     * toReadableString.
     *
     * Warning: This function is destructive!
     */
    read: function(str) {
	function err(msg) {
	    throw new Error('TimeInterval.read -- ' +
			    format.apply(null, arguments));
	}
	m = /(\d+)-(.+)/.exec(str)
	if (!m)
	    err('not a valid interval string: "%s"', str);
	var size = Number(m[1]);
	if (size >= TI_SIZES.length)
	    err('illegal size %d in interval string "%s"', size, str);
	var time = new Time(m[2]);
	this.size = size;
	this.time = time;
    },

    /*
     * Format this interval with the 'short format' given in the size
     * specification (see definition of TI_SIZES).
     */
    toShortString: function() {
	return this.time.format(this.getSize().shortFormat);
    },

    /*
     * Format this interval with the format given in the size
     * specification (see definition of TI_SIZES).
     */
    toString: function() {
	var format = this.getSize().format;
	if (typeof format == 'string') {
	    return this.time.format(format);
	} else {
	    return this.beginning().format(format[0]) +
		this.end().format(format[1]);
	}
    }
}

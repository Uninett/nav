function Calendar(idPrefix, changeCallback, interval) {
    this.idPrefix = idPrefix;
    this.changeCallback = changeCallback;
    this.interval = interval;

    this.writeInitialHTML();
    this.updateHTML();
}

Calendar.prototype = {
    idPrefix: null,
    changeCallback: null,
    interval: null,

    get time() { return this.interval.time; },
    set time(t) {
	this.interval = new TimeInterval(this.interval.size, t);
    },

    select: function(timeOrInterval) {
	if (timeOrInterval instanceof Time)
	    this.time = timeOrInterval;
	else
	    this.interval = timeOrInterval;
	this.updateHTML();
	this.changeCallback(this.time);
    },

    writeInitialHTML: function() {
	var makeCell = encapsulate(this, function(i, j) {
	    return format('<td id="%s-cell-%d,%d"></td>', this.idPrefix, i, j);
	});
	var makeRow = encapsulate(this, function(i) {
	    return format('<tr id="%s-row-%d">%s</tr>',
			  this.idPrefix, i,
			  concat(map(fix(makeCell, i), range(7))));
	});
	var monthElem = this.getElem('month');
	monthElem.innerHTML = concat(map(makeRow, range(5)));
    },
    
    updateHTML: function() {
	var cal = this;
	var now = new Time();
	var tab = this.makeMonthTable();
	var selectUnit = this.interval.getSize().unit;

	function makeSelectFunc(time) {
	    return function() { cal.select(time); };
	}

	function selectionType(unit) {
	    if (unit == 'year' || unit == 'month')
		return '';
	    if (unit == 'week')
		return 'row-selection';
	    return 'cell-selection';
	}

	function updateMovementButton(id, timeOffset) {
	    var elem = cal.getElem(id);
	    elem.onclick = makeSelectFunc(cal.time.add(timeOffset));
	    elem.setAttribute('class', 'selectable');
	}

	function todayp(t) {
	    return t.year==now.year && t.month==now.month && t.day==now.day;
	}

	function updateCell(row, col, rowSelected) {
	    var day = tab[row][col];
	    var elem = cal.getElem(format('cell-%d,%d', row, col));
	    var time = cal.time.relative(
		{day: day || (row == 0 ? 1 : cal.time.daysInMonth)});
	    var selected = (day == cal.time.day);
	    var selectable =
		!selected && !rowSelected &&
		selectUnit != 'month' &&
		(day != null || selectUnit == 'week');
	    var classes =
		(todayp(time) ? 'today ' : '') +
		(selected ? 'selected' :
		 (selectable ? 'selectable' : ''));

	    elem.innerHTML = day ? format('%d', day) : '';
	    elem.onclick = selectable ? makeSelectFunc(time) : function(){};
	    elem.className = classes;
	}

	function updateRow(row) {
	    var elem = cal.getElem('row-'+row);
	    var selected =
		(selectUnit == 'month' ||
		 (selectUnit == 'week' &&
		  cal.interval.contains(cal.time.relative(
		      {day: firstWith(identity, tab[row])}))));
	    var selectable = (selectUnit == 'week') && !selected;

	    elem.className = (selected ? 'selected' :
			      (selectable ? 'selectable' : ''));
	    for (var i = 0; i < 7; i++)
		updateCell(row, i, selected);
	}

	this.getElem().className = 'enabled';

	this.getElem('body').className =
	    selectionType(this.interval.getSize().unit);

	map(updateMovementButton,
	    ['prev-year', 'next-year', 'prev-month', 'next-month'],
	    [{year: -1},  {year: +1},  {month: -1},  {month: +1}]);

	this.getElem('header').innerHTML = this.time.format('%b %Y');

	range(5).forEach(updateRow);
    },

    getElem: function(id) {
	id = id ? (this.idPrefix+'-'+id) : this.idPrefix;
	return document.getElementById(id);
    },

    makeMonthTable: function() {
	var lastDay = this.time.daysInMonth;
	var firstWeekday = this.time.relative({day: 1}).weekDay;

	var cal = [];
	var row, col, day;
	for (row = 0, day = -firstWeekday+1; row < 5; row++) {
	    cal[row] = [];
	    for (col = 0; col < 7; col++, day++) {
		if (day < 1 || day > lastDay) {
		    cal[row][col] = null;
		} else {
		    cal[row][col] = day;
		}
	    }
	}
	return cal;
    },

    toString: function() {
	return format('<Calendar "%s", %s>',
		      this.idPrefix,
		      this.time.format('%Y-%m-%d'));
    }

};


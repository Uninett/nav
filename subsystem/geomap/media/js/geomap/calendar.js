function make_month_calendar(year, month) {
    var last_day = days_in_month(year, month);

    var first_weekday = get_weekday({year:year, month:month, day:1});

    var cal = [];
    var row, col, day;
    for (row = 0, day = -first_weekday+1; row < 5; row++) {
	cal[row] = [];
	for (col = 0; col < 7; col++, day++) {
	    if (day < 1 || day > last_day) {
		cal[row][col] = null;
	    } else {
		cal[row][col] = day;
	    }
	}
    }
    return cal;
}

function get_weekday(date) {
    var d = new Date(date.year, date.month-1, date.day);
    return (d.getDay()+6)%7;
}

function days_in_month(year, month) {
    var days = 30;
    if ((month <= 7 && month % 2 == 1) ||
	(month >= 8 && month % 2 == 0))
	days = 31;
    if (month == 2) {
	if (new Date(year, month-1, 29).getMonth() == month-1)
	    days = 29;
	else
	    days = 28;
    }
    return days;
}

function add_days(date, incr) {
    var d = {year: date.year, month: date.month, day: date.day};
    while (true) {
	if (d.day + incr < 1) {
	    d.month--;
	    if (d.month == 0) {
		d.month = 12;
		d.year--;
	    }
	    incr += d.day + days_in_month(d.year, d.month) - 1;
	    d.day = 1;
	} else if (d.day + incr > days_in_month(d.year, d.month)) {
	    incr -= days_in_month(d.year, d.month) - d.day + 1;
	    d.month++;
	    if (d.month == 13) {
		d.month = 1;
		d.year++;
	    }
	    d.day = 1;
	} else {
	    d.day += incr;
	    return d;
	}
    }    
}

function current_year() {
    return new Date().getFullYear();
}

function current_month() {
    return new Date().getMonth()+1;
}

function current_day() {
    return new Date().getDate();
}

function calendar_init(id_prefix, selection_cb, date_element) {
    var c = {id_prefix: id_prefix,
	     year: current_year(),
	     month: current_month(),
	     day: current_day(),
	     nowp: true,
	     date_element: date_element,
	     selection_cb: function() {},
	     selection_type: 'day',
	     enabled: true};
    if (date_element) {
	date_element.onchange = function() {
	    calendar_update_from_element(c);
	};
    }
    calendar_update_from_element(c);
    c.selection_cb = selection_cb;
    calendar_draw(c);
    return c;
}

function calendar_update_from_element(c) {
    var txt = c.date_element.value;
    var date_re = /(\d\d\d\d)(\d\d)((\d\d)?)/;
    var m = date_re.exec(txt);
    if (txt == 'now') {
	calendar_select_now(c);
    } else if (m) {
	calendar_select(c, m[1], m[2], m[3]=='' ? c.day : m[3]);
    } else {
	calendar_update_element(c);
    }
}

function calendar_selection_string(c) {
    return c.nowp ? 'now' : format('%04d%02d%02d', c.year, c.month, c.day);
}

function calendar_update_element(c) {
    c.date_element.value = calendar_selection_string(c);
}

function calendar_select(c, year, month, day, nowp) {
    if (nowp === undefined)
	nowp = false;
    calendar_set_date(c, year, month, day, nowp);
    if (c.date_element)
	calendar_update_element(c);
    c.selection_cb();
}

function calendar_select_now(c) {
    calendar_select(c, current_year(), current_month(), current_day(), true);
}

function calendar_deselect_now(c) {
    calendar_select(c, c.year, c.month, c.day, false);
}

function calendar_set_date(c, year, month, day, nowp) {
    c.year = year;
    c.month = month;
    c.day = day;
    c.nowp = nowp;
    calendar_draw(c);
}

function calendar_set_enabled(c, enable_p) {
    var last_value = c.enabled;
    c.enabled = enable_p;
    if (enable_p != last_value)
	calendar_draw(c);
}


function calendar_selection(c) {
    var start = {year: c.year, month: c.month, day: c.day};
    var end = {year: c.year, month: c.month, day: c.day};
    if (c.selection_type == 'week') {
	while (get_weekday(start) != 0)
	    start = add_days(start, -1);
	while (get_weekday(end) != 6)
	    end = add_days(end, 1);
    }
    return {start: start, end: end};
}

function calendar_draw(c) {
    function make_select_func(year, month, day) {
	if (c.enabled) {
	    return function() {
		calendar_select(c, year, month, day);
	    };
	} else {
	    return function() {};
	}
    }
    function get_elem(id) {
	if (id)
	    id = c.id_prefix + '-' + id;
	else
	    id = c.id_prefix;
	return document.getElementById(id);
    }

    var elem;

    elem = get_elem();
    elem.setAttribute('class', (c.enabled ? 'enabled' : 'disabled'));

    elem = get_elem('body');
    elem.setAttribute('class', (c.selection_type=='week' ?
				'row-selection' : 'cell-selection'));

    elem = get_elem('prev-year');
    elem.onclick = make_select_func(c.year-1, c.month, c.day);
    elem.setAttribute('class', 'selectable');
    elem = get_elem('next-year');
    elem.onclick = make_select_func(c.year+1, c.month, c.day);
    elem.setAttribute('class', 'selectable');

    elem = get_elem('prev-month');
    elem.onclick = make_select_func(c.month==1?c.year-1:c.year,
				    c.month==1?12:c.month-1,
				    c.day);
    elem.setAttribute('class', 'selectable');
    elem = get_elem('next-month');
    elem.onclick = make_select_func(c.month==12?c.year+1:c.year,
				    c.month==12?1:c.month+1,
				    c.day);
    elem.setAttribute('class', 'selectable');

    var month_names = ['Jan','Feb','Mar','Apr','May','Jun',
		       'Jul','Aug','Sep','Oct','Nov','Dec'];
    get_elem('header').innerHTML = format('%s %4d', month_names[c.month-1],
					  c.year);

    var month_cal = make_month_calendar(c.year, c.month);
    var row, col;
    var day = null;
    var today = {year:current_year(), month:current_month(), day:current_day()};
    for (row = 0; row < 5; row++) {
	var row_selected = false;
	for (col = 0; col < 7; col++) {
	    elem = get_elem(format('cell-%d,%d', row, col));
	    if (month_cal[row][col]) {
		day = month_cal[row][col];
		elem.onclick = make_select_func(c.year, c.month, day);
		elem.innerHTML = format('%d', day);
		var dayClass = ((c.year==today.year && c.month==today.month &&
				 day==today.day) ? 'today ' : '');
		if (day==c.day && !c.nowp) {
		    elem.setAttribute('class', dayClass + 'selected');
		    row_selected = true;
		} else {
		    elem.setAttribute('class', dayClass + 'selectable');
		}
	    } else {
		if (c.selection_type == 'week') {
		    elem.onclick = make_select_func(c.year, c.month,
						    day || 1);
		} else {
		    elem.onclick = '';
		}
		elem.innerHTML = '';
		elem.setAttribute('class', '');
	    }
	}
	get_elem('row-'+row).setAttribute('class',
					  row_selected?'selected':'selectable');
    }
}

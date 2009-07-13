var timeForm = {
    calendar: null,
    time: null,
    startTime: null,
    endTime: null,
    editMode: 'highlevel'
}

function getTimeIntervalStart() {
    var time = document.getElementById('id_starttime').value;
    if (!validate_rrd_time(time))
	alert('Invalid start time "' + time + '"');
    return time;
}

function getTimeIntervalEnd() {
    var time = document.getElementById('id_endtime').value;
    if (!validate_rrd_time(time))
	alert('Invalid end time "' + time + '"');
    return time;
}

function getTimeIntervalLength() {
    return document.getElementById('id_interval_size').value;
}


function setTimeIntervalFormListeners() {
    document.getElementById('id_endtime').onchange = updateNetData;
    document.getElementById('id_interval_size').onchange = updateNetData;
}


function validate_rrd_time(time) {
    var re_time = 'midnight|noon|teatime|\\d\\d([:.]\\d\\d)?([ap]m)?';
    var re_day1 = 'yesterday|today|tomorrow';
    var re_day2 = '(January|February|March|April|May|June|July|August|' +
	'September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|' +
        'Aug|Sep|Oct|Nov|Dec) \\d\\d?( \\d\\d(\\d\\d)?)?';
    var re_day3 = '\\d\\d/\\d\\d/\\d\\d(\\d\\d)?';
    var re_day4 = '\\d\\d[.]\\d\\d[.]\\d\\d(\\d\\d)?';
    var re_day5 = '\\d\\d\\d\\d\\d\\d\\d\\d';
    var re_day6 = 'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|' +
        'Mon|Tue|Wed|Thu|Fri|Sat|Sun';
    var re_day = format('(%s)|(%s)|(%s)|(%s)|(%s)|(%s)',
			re_day1, re_day2, re_day3, re_day4, re_day5, re_day6);
    re_ref = format('now|start|end|(((%s) )?(%s))', re_time, re_day);

    var re_offset_long = '(year|month|week|day|hour|minute|second)s?';
    var re_offset_short = 'mon|min|sec';
    var re_offset_single = 'y|m|w|d|h|s';
    var re_offset_no_sign =
	format('\\d+((%s)|(%s)|(%s))',
	       re_offset_long, re_offset_short, re_offset_single);
    re_offset =
	format('[+-](%s)([+-]?%s)*', re_offset_no_sign, re_offset_no_sign);

    re_total_str =
	format('^(%s)|((%s) ?(%s)?)$', re_offset, re_ref, re_offset);

    var re = new RegExp(re_total_str);

    return re.exec(time) != null;
}



function init_time_interval_form() {
    map(
	function(propertyAndElemId) {
	    property = propertyAndElemId[0];
	    elemId = propertyAndElemId[1];
	    timeForm[property] = document.getElementById(elemId);
	},
	[['formE', 'time-interval-form'],
	 ['intervalE', 'id_interval_size'],
	 ['dateE', 'id_date'],
	 ['timeE', 'id_timeofday'],
	 ['startE', 'id_starttime'],
	 ['endE', 'id_endtime'],
	 ['updateButtonE', 'start-end-time-update'],
	 ['editModeE', 'time-interval-edit-mode'],
	 ['highlevelPartE', 'time-interval-form-datetime'],
	 ['lowlevelPartE', 'start-end-time']]);

    //timeForm.formE.onsubmit = function() { return false; }

    timeForm.dateE.value = 'now';
    timeForm.calendar =
	calendar_init('calendar', calendar_change, timeForm.dateE);
    timeForm.time = 'now';

    timeForm.intervalE.onchange = interval_size_change;
    timeForm.intervalE.value = '5min';
    timeForm.dateE.setAttribute('style', 'display:none');
	/*
    var now = new Date();
    document.getElementById('id_timeofday').value =
	format('%s:%s', now.getHours(), Math.floor(now.getMinutes()/5)*5);
	*/
    timeForm.timeE.onchange = time_change;
    timeForm.timeE.value = timeForm.time;
    /*
    timeForm.startE.onchange = updateNetData;
    timeForm.endE.onchange = updateNetData;
    */
    timeForm.updateButtonE.onclick = updateNetData;

    setEditMode('highlevel');

    //calendar_select_now(timeForm.calendar);
    timeForm.timeE.value = timeForm.time;
    update_start_end_time();
}


function setEditMode(mode) {
    timeForm.editMode = mode;

    var mouseover_h = ' onmouseover="javascript:timeForm.highlevelPartE.setAttribute(\'class\', \'highlight\')"' +
	' onmouseout="javascript:timeForm.highlevelPartE.setAttribute(\'class\', \'\')" ';
    var mouseover_l = 'onmouseover="javascript:timeForm.lowlevelPartE.setAttribute(\'class\', \'highlight\')"' +
	' onmouseout="javascript:timeForm.lowlevelPartE.setAttribute(\'class\', \'\')" ';

    if (timeForm.editMode == 'highlevel') {
	timeForm.intervalE.removeAttribute('disabled');
	calendar_set_enabled(timeForm.calendar, true);
	timeForm.timeE.removeAttribute('readonly');
	timeForm.startE.setAttribute('readonly', 'readonly');
	timeForm.endE.setAttribute('readonly', 'readonly');
	timeForm.updateButtonE.setAttribute('style', 'display:none');
	timeForm.editModeE.innerHTML =
	    'Mode: <ul>' +
	    '<li class="selected" ' + mouseover_h + '>' +
	    'Select interval and date/time</li>' +
	    '<li ' + mouseover_l + '>' +
	    '<a href="javascript:setEditMode(\'lowlevel\')">' +
	    'Edit start/end time directly</a></li></ul>';
    } else {
	timeForm.intervalE.setAttribute('disabled', 'disabled');
	calendar_set_enabled(timeForm.calendar, false);
	timeForm.timeE.setAttribute('readonly', 'readonly');
	timeForm.startE.removeAttribute('readonly');
	timeForm.endE.removeAttribute('readonly');
	timeForm.updateButtonE.setAttribute('style', '');
	timeForm.editModeE.innerHTML =
	    'Mode: <ul>' +
	    '<li ' + mouseover_h + '>' +
	    '<a href="javascript:setEditMode(\'highlevel\')">' +
	    'Select interval and date/time</a></li>' +
	    '<li class="selected" ' + mouseover_l + '>' +
	    'Edit start/end time directly</li></ul>';
    }
}


function update_start_end_time() {
    var e_interval = document.getElementById('id_interval_size');
    var e_time = document.getElementById('id_timeofday');
    var e_start = document.getElementById('id_starttime');
    var e_end = document.getElementById('id_endtime');

    var selection = calendar_selection(timeForm.calendar);

    if (e_interval.value == '1week' || e_interval.value == '1day') {
	timeForm.startTime = format('00:00 %04d%02d%02d', selection.start.year,
			       selection.start.month, selection.start.day);
	timeForm.endTime = 'start+' + e_interval.value;
    } else {
	timeForm.startTime = 'end-' + e_interval.value;
	if (e_time.value == 'now')
	    timeForm.endTime = 'now';
	else
	    timeForm.endTime = format('%s %04d%02d%02d', e_time.value,
				      selection.end.year, selection.end.month,
				      selection.end.day);
    }
    e_start.value = timeForm.startTime;
    e_end.value = timeForm.endTime;
}

function interval_size_change() {
    var e_interval = document.getElementById('id_interval_size');

    timeForm.calendar.selection_type = e_interval.value == '1week' ? 'week' : 'day';
    calendar_draw(timeForm.calendar);

    var e_time = document.getElementById('id_timeofday').parentNode;
    if (e_interval.value == '1week' || e_interval.value == '1day') {
	e_time.setAttribute('style', 'display:none');
	calendar_deselect_now(timeForm.calendar);
    } else {
	e_time.setAttribute('style', '');
	update_start_end_time();
	updateNetData();
    }
}

function calendar_change() {
    var now = new Date();
    if (timeForm.calendar.nowp && timeForm.time != 'now') {
	timeForm.time = 'now';
	timeForm.timeE.value = timeForm.time;
    } else if (!timeForm.calendar.nowp && timeForm.time == 'now') {
	timeForm.time = format('%02d:%02d', now.getHours(),
			       Math.floor(now.getMinutes()/5)*5);
	timeForm.timeE.value = timeForm.time;
    }
    update_start_end_time();
    updateNetData();
}

function time_change() {
    var e_time = document.getElementById('id_timeofday');
    var valid
    if (e_time.value == 'now') {
	timeForm.time = timeForm.timeE.value;
	calendar_select_now(timeForm.calendar);
    } else if (/([01][0-9]|2[0-4]):[0-6][0-9]/.exec(e_time.value)) {
	timeForm.time = timeForm.timeE.value;
	calendar_deselect_now(timeForm.calendar);
    } else {
	timeForm.timeE.value = timeForm.time;
	return;
    }
}

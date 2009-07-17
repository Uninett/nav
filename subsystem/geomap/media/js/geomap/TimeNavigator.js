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
 * TimeNavigator.js: Provides time navigation in a manner similar to
 * that in Stager (http://software.uninett.no/stager/).
 */


function TimeNavigator(idPrefix, changeCallback, initialInterval) {
    this.idPrefix = idPrefix;
    if (initialInterval)
	this.interval = initialInterval;
    else
	this.interval = new TimeInterval(TI_5MIN);

    this.onChange = makeHook();
    if (changeCallback)
	addHook(this.onChange, changeCallback);

    var dateSelectable = encapsulate(this, function(time) {
	return this.interval.gotoTime(time).selectable();
    });
    function monthSelectable(time) {
	return new TimeInterval(TI_MONTH, time).selectable();
    }
    this.calendar = new Calendar(idPrefix+'-calendar',
				 encapsulate(this, this.calendarChanged),
				 this.interval,
				 dateSelectable, monthSelectable);

    this.updateUI();
}

TimeNavigator.prototype = {
    /*
     * Selected time interval (TimeInterval object).
     */
    interval: null,

    /*
     * Hook called with the new interval as argument each time the
     * selection is changed. (use addHook to add more functions to
     * this).
     */
    onChange: null,

    /*
     * Common prefix of id attribute of all HTML elements to be
     * manipulated by this TimeNavigator.
     */
    idPrefix: null,

    calendar: null,

    /*
     * Select a new interval.
     */
    setInterval: function(newInterval) {
	this.interval = newInterval;
	this.updateUI();
	callHook(this.onChange, newInterval);
    },

    /*
     * Update the user interface (i.e. HTML elements) to reflect the
     * currently selected interval.
     */
    updateUI: function() {

	var getElem = encapsulate(this, function(id) {
	    return document.getElementById(this.idPrefix + '-' + id);
	});

	var makeIntervalUpdater =
	    (function (setInterval) {
		return function(func) { return compose(setInterval, func) };
	    })(encapsulate(this, this.setInterval));

	var updateButton = encapsulate(this, function(button) {
	    var elem = getElem(button.id);
	    var enabled =
		button.enable==true || callMethod(this.interval,
						  button.enable);
	    var label = button.label(this.interval);
	    var activate =
		makeIntervalUpdater(encapsulateMethod(this.interval,
						      button.method));

	    elem.className = enabled ? 'enabled' : 'disabled';
	    elem.setAttribute('title', label);
	    //elem.innerHTML = label;
	    elem.onclick = enabled ? activate : function(){};
	});

	function makeHTMLOptions(options) {
	    function optionHTML(option) {
		var value = option[0];
		var name = option[1];
		if (value != null)
		    return format('<option value="%s">%s</option>',
				  value, name);
		return format('<option>%s</option>', name);
	    }
	    return concat(map(optionHTML, options));
	}

	// Display the currently selected time interval:
	getElem('selected-time').innerHTML = this.interval.toString();

	// Update actions, labels and enabledness of navigation buttons:
	this.buttons.forEach(updateButton);

	// Create menu for selecting smaller intervals:
	var downElem = getElem('down');
	var choices = this.interval.downChoices();
	if (choices) {
	    var choiceSize = this.interval.smallerSize();
	    var options = arrayConcat(
		[[[null, sizeName(choiceSize, true) + '...']],
		 zip(range(choices.length),
		     mapMethod('toShortString', choices))]);
	    downElem.innerHTML = makeHTMLOptions(options);
	    downElem.className = 'enabled';
	} else {
	    downElem.innerHTML = '';
	    downElem.className = 'disabled';
	}
	downElem.onchange = makeIntervalUpdater(function () {
	    return choices[downElem.value];
	});

	// Create interval size selection menu:
	var sizeElem = getElem('interval-size');
	var sizeOptions = subarray(zip(range(TI_SIZES.length),
				       map(fix(sizeName, true, 1), TI_SIZES)),
				   1);
	sizeElem.innerHTML = makeHTMLOptions(sizeOptions);
	sizeElem.value = this.interval.size;
	sizeElem.onchange = makeIntervalUpdater(encapsulate(this, function() {
	    return new TimeInterval(Number(sizeElem.value),
				    this.interval.time);
	}));

	// Update calendar:
	this.calendar.interval = this.interval;
	this.calendar.updateHTML();
    },

    calendarChanged: function() {
	this.setInterval(this.calendar.interval);
    },

    buttons: [
	{id: 'prev-jump', method: 'prevJump', enable: true,
	 label: function(ti) {
	     return 'Go back ' + sizeName(ti.largerSize()) }},
	{id: 'prev', method: 'prev', enable: true,
	 label: function(ti) {
	     return 'Go back ' + sizeName(ti.getSize()) }},
	{id: 'next', method: 'next', enable: 'nextPossible',
	 label: function(ti) {
	     return 'Go forward ' + sizeName(ti.getSize()) }},
	{id: 'next-jump', method: 'nextJump', enable: 'nextJumpPossible',
	 label: function(ti) {
	     return 'Go forward ' + sizeName(ti.largerSize()) }},
	{id: 'last', method: 'last', enable: 'nextPossible',
	 label: function(ti) {
	     return 'Go to last ' + sizeName(ti.getSize(), true) }},
	{id: 'up', method: 'up', enable: 'upPossible',
	 label: function(ti) {
	     if (ti.upPossible())
		 return 'Go up to ' + sizeName(ti.largerSize(), true);
	     return ''; }}
    ]

};

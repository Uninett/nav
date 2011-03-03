/* Subsystem JavaScripts for NAV
 *
 * Copyright (C) 2003-2004 Norwegian University of Science and Technology
 * Copyright (C) 2006 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 2 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 *
 */

function changeDisplay(elementId, setTo) {
	if (document.getElementById) {
		// DOM
		var theElement = document.getElementById(elementId);
	} else {
		if (document.all) {
			// Proprietary DOM
			var theElement = document.all[elementId];
		} else {
			// Create an object to prevent errors further on
			var theElement = new Object();
		}
	}
	if (!theElement) {
		/* The page has not loaded or the browser claims to support
		document.getElementById or document.all but cannot actually
		use either */
		return;
	}
	// Reference the style ...
	if (theElement.style) {
		theElement = theElement.style;
	}
	if (typeof(theElement.display) == 'undefined' &&
	 !(window.ScriptEngine && ScriptEngine().indexOf('InScript') + 1 )) {
		// The browser does not allow us to change the display style
		// Alert something sensible (not what I have here ...)
		window.alert('Your browser is crap');
		return;
	}
	// Change the display style
	theElement.display = setTo;
}

function showPorts(elementId) {
	known = ['activeports', 'portstatus', 'gwportstatus'];
	for (i=0;i<known.length;i++) {
		changeDisplay(known[i], known[i] == elementId ? 'block' : 'none');
	}
}

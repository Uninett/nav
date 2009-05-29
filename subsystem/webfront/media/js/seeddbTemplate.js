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

function updateDisplay(select) {
	var options = select.options;
	for (optIndex = 0; optIndex < options.length; optIndex++) {
		option = options.item(optIndex);
		setElementDisplay(option.value,option.selected);
	}	
}

function setElementDisplay(elementId,display) {
	if (document.getElementById) {
		var element = document.getElementById(elementId);
		if (element) {
			if (display) {
				element.style.display = '';
			} else {
				element.style.display = 'none';
			}
		}
	}
}

function toggleDisabled(select,elementId) {
	var options = select.options;
	var somethingSelected = false;
	for (optIndex = 0; optIndex < options.length; optIndex++) {
		option = options.item(optIndex);
		if (option.selected == true) {
			somethingSelected = true;
			break;
		}
	}	
	if (document.getElementById) {
		var element = document.getElementById(elementId);
		if (somethingSelected = true) {
			element.disabled = false;
		} else {
			element.disabled = true;
		}
	}
}

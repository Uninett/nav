/* Subsystem JavaScripts for NAV
 *
 * Copyright 2003-2004 Norwegian University of Science and Technology
 * Copyright 2006 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * 
 * Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
 *          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
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

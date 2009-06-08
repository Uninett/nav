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

function checkForm(form) {
	if (form.title.value == "") {
		alert("Please fill in a title.");
		form.title.focus();
	} else if (form.description.value == "") {
		alert("Please fill in a description.");
		form.description.focus();
	} else {
		return true;
	}
	return false;
}

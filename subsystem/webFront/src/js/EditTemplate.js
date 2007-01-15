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
 * Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
 *          Magnar Sveen <magnars@idi.ntnu.no>
 *          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
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

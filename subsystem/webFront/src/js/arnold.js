/* Arnold-specific javascripts
 *
 * Copyright 2003-2005 Norwegian University of Science and Technology
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
 * Author: John-Magne Bredal <john.m.bredal@ntnu.no>
 *
 */


/*
 * Specific for creating new or editing existing blocktypes.
 */
function validateForm() {
    if (document.blockform.blocktitle.value == "") {
	alert("Please fill in the title for the block.");
	document.blockform.blocktitle.focus();
	return false;
    }

    var newreasonvalue = /^--/;

    if (document.blockform.reasonid.selectedIndex == 0 && document.blockform.newreason.value.search(newreasonvalue) == 0) {
	alert("Please select a (or create a new) reason.");
	return false;
    }

    if (document.blockform.duration.value == "") {
	alert("Please fill in block duration");
	document.blockform.duration.focus();
	return false;
    }

    return true;

}

/* JavaScripts for Alert the Profiles subsystem in NAV
 *
 * Copyright 2008 UNINETT AS
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
 * You should have received a copy of the GNU General Public
 * License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 * 02111-1307  USA
 *
 * Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
 *
 */

$(function() {
	// Highlights shared time-periods
	var doHighlight = function() {
		// The last class should (in theory) be the "shared_period"
		// class
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).addClass('hilight');
	}
	// Removes highlight from shared time-periods
	var removeHighlight = function() {
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).removeClass('hilight');
	}
	$("#timeperiods_table_container tr.all_days_period").hover(doHighlight, removeHighlight);

	// Switch between multiple and single select list in the expression form
	var switchMultiple = function() {
		if ($("select#id_operator").val() == 11) {
			$("select#id_value").attr('multiple', 'multiple');
		} else {
			$("select#id_value").removeAttr('multiple');
		}
	}
	$("select#id_operator").ready(switchMultiple);
	$("select#id_operator").change(switchMultiple);

	// Check multiple checkboxes for shared periods
	var checkMultiple = function() {
		// The last class is "hilight", the second last is the
		// "shared_period" class
		var shared_id = $(this).parents("tr").attr('class').split(' ').slice(-2, -1);
		var checked = $(this).attr('checked');
		if (checked == undefined) {
			$("tr." + shared_id + " input").removeAttr('checked');
		} else {
			$("tr." + shared_id + " input").attr('checked', 'checked');
		}
	}
	$("#timeperiods_table_container tr.all_days_period input").click(checkMultiple);

	// Display some help text to the "highlight shared periods" js
	$("#timeperiods_table_container").prepend("<div class=\"boxes infobox\"><p>" +
		"If, when hovering over one period in one of the tables, two rows " +
		"in different tables are highlighted, those two periods are " +
		"actually the one and same period. It's just an \"all days\" period." +
	"</p></div>");
});

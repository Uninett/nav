/* JavaScripts for Alert the Profiles subsystem in NAV
 *
 * Copyright (C) 2008 UNINETT AS
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
 *
 */

require([], function() {

    var containerSelector = "#timeperiods_table_container";
    
    // Highlights shared time-periods
    var doHighlight = function() {
	// The last class should (in theory) be the "shared_period"
	// class
	var shared_id = $(this).attr('class').split(' ').slice(-1);
	$("." + shared_id).addClass('hilight');
    };

    // Removes highlight from shared time-periods
    var removeHighlight = function() {
	var shared_id = $(this).attr('class').split(' ').slice(-1);
	$("." + shared_id).removeClass('hilight');
    };

    // Switch between multiple and single select list in the expression form
    var switchMultiple = function() {
	if ($("select#id_operator").val() === "11") {
	    $("select#id_value").attr('multiple', 'multiple');
	} else {
	    $("select#id_value").removeAttr('multiple');
	}
    };


    /**
     * When toggling a period that is shared with another period, toggle the
     * other period aswell.
     */
    var checkMultiple = function() {
        var that = this,
            sharedClass = $(this).closest('td').attr('class'),
            selector = '.' + sharedClass + ' input';
        
        $(containerSelector).find(selector).filter(function() {
            return this !== that;
        }).prop('checked', this.checked);
    };

    $(function() {
        var $timePeriods = $(containerSelector).find("tr.all_days_period"),
            $operator = $("select#id_operator");
	$timePeriods.hover(doHighlight, removeHighlight);
	$timePeriods.find("input").click(checkMultiple);
	$operator.ready(switchMultiple);
	$operator.change(switchMultiple);
    });

});

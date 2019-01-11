/* JavaScripts for Alert the Profiles subsystem in NAV
 *
 * Copyright (C) 2008 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 3 as published by the Free
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
    

    /**
     * Finds and returns the class that starts with 'period_' for the given
     * element. The class is prepended a dot (.) for use in jQuery selectors.
     *
     * @param {HTMLElement} element Element that has the class
     */
    var findSharedClass = function(element) {
        return element.className.split(' ').filter(function(klass){
            return klass.match(/period_/);
        }).map(function(klass) {
            return '.' + klass;
        }).join(' ');        
    };
    

    /**
     * Highlights shared time-periods
     */
    var doHighlight = function() {
        $(findSharedClass(this)).addClass('hilight');
    };


    /**
     * Removes highlight from shared time-periods
     */
    var removeHighlight = function() {
        $(findSharedClass(this)).removeClass('hilight');
    };

    
    /**
     * Switch between multiple and single select list in the expression form
     */
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

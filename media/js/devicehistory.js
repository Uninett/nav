/* Copyright (C) 2008-2009 UNINETT AS
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

$(document).ready(function() {
        $("ul.email_message").hide();

		$("li.sms_message").each(function(i) {
					var id = $(this).attr("id").split("_").slice(-1);
					$("ul#email_" + id).before("<a id=\"#email_" + id + "\" class=\"expand_link\">Expand</a>");
		});

		$("a.expand_link").toggle(function() {
                    $(this).text("Hide");
					var id = $(this).attr("id").split("_").slice(-1);
					$("ul#email_" + id).show("normal");
		}, function() {
                    $(this).text("Expand");
					var id = $(this).attr("id").split("_").slice(-1);
					$("ul#email_" + id).hide("normal");
        });
});

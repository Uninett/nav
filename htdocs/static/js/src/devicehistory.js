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

require(['plugins/quickselect', 'libs/jquery'], function (QuickSelect) {
    $(document).ready(function() {
        new QuickSelect('.quickselect');

        var showText = "Show email",
            hideText = "Hide email";

        $("ul.email_message").hide();

        $("li.sms_message").each(function(i) {
            var id = getPartialId(this),
                button = $('<a/>').attr('id', '#email_' + id).addClass('expand_link button tiny').text(showText);

            $("ul#email_" + id).before(button);
        });

        $("a.expand_link").toggle(function() {
            $(this).text(hideText);
            $("ul#email_" + getPartialId(this)).show("normal");
        }, function() {
            $(this).text(showText);
            $("ul#email_" + getPartialId(this)).hide("normal");
        });
    });

    function getPartialId(element) {
        /* Get the part of the elements id after underscore */
        return $(element).attr("id").split("_").slice(-1);
    }

});

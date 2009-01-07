/* Quickselect JavaScripts for NAV
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
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 * 
 * Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
 */

$(function() {
    $('.quickselect').each(function() {
        var quickselect = $(this);
        var search     = $('<label>Search <textarea class="search" rows="2"></textarea></label>');
        var all        = $('<input type="button" value="Select all" />');
        var spinner    = $('<img src="/images/main/process-working.gif" alt="" style="vertical-align: middle; visibility: hidden;"/>');
        var timeout    = null;

        var selects = quickselect.find('select');
        var selects_clone = selects.clone()

        function do_search(value) {
            /*
             * Search code that does OR search in optgroup and options.
             *
             *   option matches   -> it and any parent optgroup is shown.
             *   optgroup matches -> it and all children are shown.
             */
            var keywords = value.replace("'","").split(/\s+/);

            quickselect.find('label').removeClass('highlight');

            // Search on clone of select and replace selects children with
            // cloned children
            for (var j = 0; j < selects.length; j++) {
                var select = selects.eq(j);
                var clone  = selects_clone.eq(j).clone();

                if (keywords[0] == '') {
                    // Show all options when our search is empty
                    select.children().remove();
                    select.append(clone.children());

                } else {
                    for (var i = 0; i < keywords.length; i++) {
                        if(keywords[i]) {
                            // Show options and its parents if it contains a keyword
                            clone.find("option:contains('" + keywords[i] + "')").addClass('keep').parents('optgroup').addClass('keep');
                            clone.find("optgroup[label*='" + keywords[i] + "']").addClass('keep').find('option').addClass('keep');
                        }
                    }

                    clone.find(":not(.keep)").remove();
                    select.children().remove();
                    select.append(clone.children());


                    select.find('option:visible').parents('select').siblings('label').addClass('highlight');
                }
            }
            spinner.css('visibility', 'hidden');
        };

        function handler() {
            /*
             * Event handler for search field, uses a timeout to avoid starting
             * the searh before the user is done typing.
             */
            var value = $(this).val();
            if (timeout) {
                clearTimeout(timeout);
            }

            timeout = setTimeout(function() { do_search(value) }, 300);

            if (value.length > 0) {
                spinner.css('visibility', 'visible');
            }
        }
        search.find('.search').keyup(handler).click(handler);

        // Collapse and selects that we dont want to show
        quickselect.find('.collapse').children().not('label').hide()

        // Add clik handler and state indicator for label.
        quickselect.find('div label').each(function() {
            var down = $('<span>&darr; </span>');
            var up = $('<span>&uarr; </span>');

            if ($(this).parent().hasClass('collapse')) {
                up.hide();
            } else {
                down.hide();
            }

            $(this).prepend(up).prepend(down).css('cursor', 'pointer')

            $(this).click(function() {
                down.toggle();
                up.toggle();

                $(this).parent().children().not('label').toggle();
                $(this).parent().find('option:selected').removeAttr('selected');
            });
        });

        // Add select all buttons
        selects.each(function (){
            var select = $(this);

            select.attr('size', 10);

            if (select.attr('multiple')) {
                var clone  = all.clone();
                clone.click(function() {
                    select.find('option:visible').attr('selected', 'selected');
                });
                select.parent().find('input').after(clone);
            }
        });

        // Fix the search box with to match selects and insert the search box
        search.find('.search').css('width', quickselect.find('select').width() + 'px')
        search.find('.search').before(spinner);
        quickselect.prepend(search);
    });
});

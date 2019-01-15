/* Quickselect JavaScripts for NAV
 *
 * Copyright (C) 2008 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 3 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 *
 */
define([], function() {

    /* Todo: Rewrite this to not be so DOM-manipulative */

    var html = {
        downArrow: '<span class="downarrow">&darr; </span>',
        upArrow: '<span class="uparrow">&uarr; </span>',
        selectAllButton: '<input type="button" value="Select all" />'
    };

    function QuickSelect(node) {
        this.node = typeof node === 'string' ? $(node) : node;
        this.textAreas = this.node.find('div select');

        var searchArea = addLabelAndSearch(this.node, this.textAreas);
        addTextAreaListener(this.textAreas, searchArea);
        addSelectAllButtons(this.textAreas);
        setTextAreaSize(this.textAreas);
        addArrows(this.node);
        collapseNodes(this.node);
    }

    function addLabelAndSearch(node, textAreas) {
        var label = $('<label>Search</label>');
        var searchArea = $('<textarea class="search" rows="2"></textarea>');
        var textAreaWidth = textAreas.find('select').width();

        searchArea.css('width', textAreaWidth);
        label.append(searchArea);
        node.prepend(label);

        return searchArea;
    }

    function addTextAreaListener(textAreas, searchArea) {
        searchArea.keyup([textAreas, textAreas.clone()], do_search);
    }

    function addSelectAllButtons(textAreas) {
        textAreas.each(function() {
            var textArea = $(this);

            if (textArea.attr('multiple')) {
                var selectAllButton = $(html.selectAllButton);
                selectAllButton.click(function () {
                    textArea.find('option').attr('selected', 'selected');
                });
                textArea.parent().find('input').after(selectAllButton);
            }
        });
    }

    function setTextAreaSize(textAreas) {
        textAreas.attr('size', 10);
    }

    function addArrows(node) {
        $('div label', node).each(function () {
            var up = $(html.upArrow);
            var down = $(html.downArrow);

            $(this).prepend(up).prepend(down).css('cursor', 'pointer');

            if ($(this).parent('div').hasClass('collapse')) {
                up.hide();
            } else {
                down.hide();
            }

            $(this).click(function () {
                down.toggle();
                up.toggle();

                $(this).parent().children().not('label').toggle();
                $(this).parent().find('option:selected').removeAttr('selected');
            });

        });
    }

    function collapseNodes(node) {
        $('.collapse', node).children().not('label').hide();
    }

    function do_search(event) {
        /*
         * Search code that does OR search in optgroup and options.
         *
         *   option matches   -> it and any parent optgroup is shown.
         *   optgroup matches -> it and all children are shown.
         */
        var value = $(this).val();
        var keywords = value.replace("'", "").split(/\s+/);

        var selects = event.data[0];
        var selects_clone = event.data[1];

        // Search on clone of select and replace selects children with
        // cloned children
        for (var j = 0; j < selects.length; j++) {
            var select = selects.eq(j);
            var clone = selects_clone.eq(j).clone();

            if (keywords[0] === '') {
                // Show all options when our search is empty
                select.children().remove();
                select.append(clone.children());

            } else {
                for (var i = 0; i < keywords.length; i++) {
                    if (keywords[i]) {
                        // Show options and its parents if it contains a keyword
                        clone.find("option:contains('" + keywords[i] + "')").addClass('keep').parents('optgroup').addClass('keep');
                        clone.find("optgroup[label*='" + keywords[i] + "']").addClass('keep').find('option').addClass('keep');
                    }
                }

                clone.find(":not(.keep)").remove();
                select.children().remove();
                select.append(clone.children());
            }
        }

    }

    return QuickSelect;

});

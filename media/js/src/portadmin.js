require(['libs/spin.min', 'libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {

    if(!Array.indexOf){
        Array.prototype.indexOf = function(obj){
            for(var i=0; i<this.length; i++){
                if (this[i] === obj) {
                    return i;
                }
            }
            return -1;
        };
    }

    var nav_ajax_queue = [];  // Queue for rows we are saving
    var queue_data = {};  // Object containing data for ajax requests

    /* Generic spinner created for display in the middle of a cell */
    var spinner = new Spinner({length: 3, width: 2, radius: 5});


    $(document).ready(function(){
        NAV.addGlobalAjaxHandlers();

        var interfaceTable = $('#portadmin-interfacecontainer');
        var infoBox = $('#infobox');

        if (interfaceTable.length) {
            addTrunkSelectedListener(interfaceTable);
            addChangeListener(interfaceTable);
            addSaveListener(interfaceTable);
            addSaveAllListener(interfaceTable);
            addUndoListener(interfaceTable);
            addToggleVlanInfoListener(infoBox);
        }
    });

    /*
     * If user selects the trunk value in a drop-down list, the user shall
     * be redirected to the trunk edit page.
     */
    function addTrunkSelectedListener(table) {
        $(table).find('.vlanlist').on('change click', function (event) {
            var $select = $(this);
            if ($select.val() === 'trunk') {
                event.stopPropagation();
                location.href = $select.find(':selected').attr('data-url');
            }
        });
    }

    /*
     * Add changelisteners to the tbody element to avoid adding 3
     * listeners for each row. Also split up events to avoid acting
     * on irrelevant changes.
     */
    function addChangeListener(table) {
        $(table).find('tbody').on('keyup change', '.ifalias', function (event) {
            actOnChange($(event.target).parents('tr'));
        });
        $(table).find('tbody').on('change', '.vlanlist', function (event) {
            actOnChange($(event.target).parents('tr'));
        });
        $(table).find('tbody').on('click', '.voicevlan', function (event) {
            actOnChange($(event.target).parents('tr'));
        });
    }

    /*
     * Mark row changed or not based on values in row
     */
    function actOnChange(row) {
        if (textFieldChanged(row) || dropDownChanged(row) || voiceVlanChanged(row)) {
            markAsChanged(row);
        } else {
            markAsUnchanged(row);
        }
    }

    function addSaveListener(element) {
        /*
        Save when clicking on the save buttons. As the save button is in
        another row than the form, find the correct row and run save on it.
        */
        $('.save', element).click(function (event) {
            var motherId = $(event.target).parents('tr').attr('data-mother-row');
            saveRow.call($('#' + motherId));
        });
    }

    function addSaveAllListener(element) {
        $('.saveall_button').click(bulkSave);
    }

    function bulkSave() {
        $("tr.changed").each(saveRow);
    }

    /*
     * Undo the changes the user has done on the form fields
     */
    function addUndoListener(element) {
        $('.undo', element).click(function (event) {
            var motherId = $(event.target).parents('tr').attr('data-mother-row');
            var $row = $('#' + motherId);
            var $ifalias = $row.find(".ifalias");
            var $vlan = $row.find(".vlanlist");
            var $voicevlan = $row.find(".voicevlan");

            // Set ifalias back to original value
            $ifalias.val($ifalias.attr('data-orig'));

            // Set vlan back to original value
            $vlan.val($('[data-orig]', $vlan).val());

            // Check or uncheck telephone checkbox
            if ($voicevlan.length) {
                if ($voicevlan.attr('data-orig').toLowerCase() === 'true') {
                    $voicevlan.prop('checked', 'checked');
                } else {
                    $voicevlan.prop('checked', false);
                }
            }

            clearChangedState($row);
        });
    }

    function addToggleVlanInfoListener(element) {
        // Toggler for the available vlans list
        $('.toggler', element).click(function () {
            var vlanlist = $('ul', element),
                expandButton = $('.toggler.expand'),
                collapseButton = $('.toggler.collapse');

            if (vlanlist.is(':visible')) {
                vlanlist.hide();
                expandButton.removeClass('hidden');
                collapseButton.addClass('hidden');
            } else {
                vlanlist.show();
                expandButton.addClass('hidden');
                collapseButton.removeClass('hidden');
            }
        });
    }

    function textFieldChanged(row) {
        var element = $(row).find(".ifalias");
        return $(element).attr('data-orig') !== $(element).val();
    }

    function dropDownChanged(row) {
        var dropdown = $(row).find(".vlanlist");
        var origOption = $('[data-orig]', dropdown)[0];
        var selectedOption = $('option:selected', dropdown)[0];
        return origOption !== selectedOption;
    }

    function voiceVlanChanged(row) {
        /*
         * XOR checkbox checked and original value to see if changed
         */
        var $checkbox = $(row).find('.voicevlan');
        if ($checkbox.length) {
            var origOption = $checkbox.attr('data-orig').toLowerCase() === 'true';
            var checkedValue = $checkbox.prop('checked');
            return checkedValue ^ origOption;
        } else {
            return false;
        }
    }

    function markAsChanged(row) {
        var $row = $(row);
        if (!$row.hasClass('changed')) {
            showActionRow($row);
            $row.addClass("changed");
        }
    }

    function showActionRow($row) {
        /* Slide down the actionrow */
        $($row.nextAll('.actionrow')[0]).find('.slider').slideDown();
    }

    function markAsUnchanged(row) {
        var $row = $(row);
        if ($row.hasClass('changed')) {
            hideActionRow($row);
            $row.removeClass("changed");
        }
    }

    function hideActionRow($row) {
        $($row.nextAll('.actionrow')[0]).find('.slider').slideUp();
    }

    function clearChangedState(row) {
        markAsUnchanged(row);
    }

    function saveRow() {
        /*
         * This funcion does an ajax call to save the information given by the user
         * when the save-button is clicked.
         */

        var $row = $(this);
        if (!$row.is('tr')) {
            $row = $row.parents('tr');
        }

        var rowid = $row.prop('id');
        if (!rowid) {
            console.log('Could not find id of row ' + $row);
            return;
        }

        // Post data and wait for json-formatted returndata. Display status information to user
        saveInterface($row, create_ajax_data($row));
    }

    function create_ajax_data($row) {
        /*
         Create the object used in the ajax call.
         */
        var data = {};
        data.interfaceid = $row.prop('id');
        if (textFieldChanged($row)) {
            data.ifalias = $row.find(".ifalias").val();
        }
        if (dropDownChanged($row)) {
            data.vlan = $row.find(".vlanlist").val();
        }
        if (voiceVlanChanged($row)) {
            data.voicevlan = $row.find(".voicevlan").prop('checked');
        }
        if ($row.find(".voicevlan").prop('checked')) {
            data.voice_activated = true;
        }
        return data;
    }

    function saveInterface($row, interfaceData) {
        var rowid = $row.prop('id');
        // If a save on this row is already in progress, do nothing.
        if (nav_ajax_queue.indexOf(rowid) > -1) {
            return;
        }
        disableSaveallButtons();
        nav_ajax_queue.push(rowid);
        queue_data[rowid] = interfaceData;

        // Do not send more than one request at the time.
        if (nav_ajax_queue.length > 1) {
            return;
        }

        doAjaxRequest(rowid);
    }

    function doAjaxRequest(rowid) {
        var $row = $('#' + rowid);
        var interfaceData = queue_data[rowid];
        var actionCell = $($row.nextAll('.actionrow')[0]).find('td').get(0);
        $.ajax({url: "save_interfaceinfo",
            data: interfaceData,
            dataType: 'json',
            type: 'POST',
            beforeSend: function () {
                $('tr.error').remove();
                disableButtons(actionCell);
                spinner.spin(actionCell);
            },
            success: function () {
                clearChangedState($row);
                indicateSuccess($row);
                updateDefaults($row, interfaceData);
            },
            error: function (jqXhr) {
                console.log(jqXhr.responseText);
                indicateError($row, $.parseJSON(jqXhr.responseText).messages);
            },
            complete: function (jqXhr) {
                removeFromQueue(rowid);
                enableButtons(actionCell);
                spinner.stop();
                if (nav_ajax_queue.length === 0) {
                    enableSaveallButtons();
                } else {
                    // Process next entry in queue
                    doAjaxRequest(nav_ajax_queue[0]);
                }
            }
        });
    }

    function disableButtons(cell) {
        $(cell).find('button').prop('disabled', true);
    }

    function enableButtons(cell) {
        $(cell).find('button').prop('disabled', false);
    }

    function indicateSuccess($row) {
        /* Animate row to indicate success */
        var $cells = $row.find('td');

        $row.addClass('success');
        $cells.animate({'background-color': '#FFF'}, 1000, function () {
            $cells.removeAttr('style');
            $row.removeClass('success');
        });
    }

    function indicateError($row, messages) {
        var $newRow = $('<tr/>').addClass('error'),
            $cell = $('<td class="" colspan="10"/>'),
            $message = $('<span/>');

        var error = '';
        for (var x = 0, l = messages.length; x < l; x++) {
            error += messages[x].message + '. ';
        }
        $message.text(error);

        $newRow.append($cell.append($message));
        $newRow.insertAfter($row);

        $newRow.click(function () {
            $(this).hide(1000, function () {
                $(this).remove();
            });
        });
    }

    function updateDefaults($row, data) {
        if ('ifalias' in data) {
            updateIfAliasDefault($row, data.ifalias);
        }
        if ('vlan' in data) {
            updateVlanDefault($row, data.vlan);
        }
        if ('voicevlan' in data) {
            updateVoiceDefault($row, data.voicevlan);
        }
    }

    function updateIfAliasDefault($row, ifalias) {
        var old_ifalias = $row.find(".ifalias").attr('data-orig');
        if (old_ifalias !== ifalias) {
            $row.find(".ifalias").attr('data-orig', ifalias);
        }
    }

    function updateVlanDefault($row, vlan) {
        var old_vlan = $row.find('option[data-orig]').val();
        if (old_vlan !== vlan) {
            console.log('Updating vlan default from ' + old_vlan + ' to ' + vlan);
            $row.find('option[data-orig]').removeAttr('data-orig');
            $row.find('option[value=' + vlan + ']').attr('data-orig', vlan);
        }
    }

    function updateVoiceDefault($row, new_value) {
        var $voice_element = $row.find(".voicevlan");
        if ($voice_element.length) {
            var old_value = $voice_element.attr('data-orig');
            if (old_value !== new_value) {
                $voice_element.attr('data-orig', new_value);
            }
        }
    }

    function removeFromQueue(id) {
        delete queue_data[id];
        var index = nav_ajax_queue.indexOf(id);
        if (index > -1) {
            nav_ajax_queue.splice(index, 1);
        }
    }

    function disableSaveallButtons() {
        $("input.saveall_button").attr('disabled', 'disabled');
    }

    function enableSaveallButtons() {
        $("input.saveall_button").removeAttr('disabled');
    }

});


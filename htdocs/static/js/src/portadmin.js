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

    var nav_ajax_queue = [];  // Queue for cards we are saving
    var queue_data = {};  // Object containing data for ajax requests

    /* Mapping for ifadminstatus */
    var ifAdminStatusMapping = {
        1: true,
        2: false
    };

    /* Generic spinner created for display in the middle of a cell */
    var spinner = new Spinner({length: 3, width: 2, radius: 5});
    var parentSelector = '.port_row';

    $(document).ready(function(){
        var $wrapper = $('#portadmin-wrapper');

        if ($wrapper.length) {
            addTrunkSelectedListener($wrapper);
            addChangeListener($wrapper);
            addSaveListener($wrapper);
            addSaveAllListener($wrapper);
        }
    });

    /*
     * If user selects the trunk value in a drop-down list, the user shall
     * be redirected to the trunk edit page.
     */
    function addTrunkSelectedListener($wrapper) {
        $wrapper.find('.vlanlist').on('change click', function (event) {
            var $select = $(this);
            if ($select.val() === 'trunk') {
                event.stopPropagation();
                location.href = $select.find(':selected').attr('data-url');
            }
        });
    }

    /*
     * Add changelisteners the wrapper. Also split up events to avoid acting
     * on irrelevant changes.
     */
    function addChangeListener($wrapper) {
        $wrapper.on('keyup change', '.ifalias', function (event) {
            actOnChange($(event.target).parents(parentSelector));
        });
        $wrapper.on('change', '.vlanlist', function (event) {
            actOnChange($(event.target).parents(parentSelector));
        });
        $wrapper.on('click', '.voicevlan', function (event) {
            actOnChange($(event.target).parents(parentSelector));
        });
        $wrapper.on('change', '.ifadminstatus', function (event) {
            actOnChange($(event.target).parents(parentSelector));
        });
    }

    /*
     * Mark card changed or not based on values in card
     */
    function actOnChange(row) {
        if (textFieldChanged(row) || dropDownChanged(row) || voiceVlanChanged(row) || adminStatusChanged(row)) {
            markAsChanged(row);
        } else {
            markAsUnchanged(row);
        }
    }

    function addSaveListener($wrapper) {
        /* Save when clicking on the save buttons. */
        $wrapper.on('click', '.portadmin-save', function (event) {
            var $row = $(event.target).parents(parentSelector);
            saveRow($row);
        });
    }

    function addSaveAllListener(element) {
        $('.saveall_button').click(bulkSave);
    }

    function bulkSave() {
        $(".changed").each(function (index, card) {
            saveRow($(card));
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

    function adminStatusChanged(row) {
        var $checkbox = $(row).find('.ifadminstatus');
        if ($checkbox.length) {
            var origOption = ifAdminStatusMapping[$checkbox.attr('data-orig')];
            var checkedValue = $checkbox.prop('checked');
            return origOption ^ checkedValue;
        } else {
            return false;
        }
    }

    function markAsChanged(row) {
        var $row = $(row);
        if (!$row.hasClass('changed')) {
            $row.find('.portadmin-save').removeClass('secondary');
            $row.addClass("changed");
        }
    }

    function markAsUnchanged(row) {
        var $row = $(row);
        if ($row.hasClass('changed')) {
            $row.find('.portadmin-save').addClass('secondary');
            $row.removeClass("changed");
        }
    }

    function clearChangedState(row) {
        markAsUnchanged(row);
    }

    function saveRow($row) {
        /*
         * This funcion does an ajax call to save the information given by the user
         * when the save-button is clicked.
         */

        var rowid = $row.prop('id');
        if (!rowid) {
            console.log('Could not find id of card ' + $row);
            return;
        }

        // Post data and wait for json-formatted returndata. Display status information to user
        saveInterface(create_ajax_data($row));
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
        if (adminStatusChanged($row)) {
            var adminStatusChecked = $row.find(".ifadminstatus").prop('checked');
            if (adminStatusChecked) {
                data.ifadminstatus = 1;
            } else {
                data.ifadminstatus = 2;
            }
        }
        if ($row.find(".voicevlan").prop('checked')) {
            data.voice_activated = true;
        }
        return data;
    }

    function saveInterface(interfaceData) {
        var rowid = interfaceData.interfaceid;
        console.log('Saving interface with id ' + rowid);
        // If a save on this card is already in progress, do nothing.
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
        $.ajax({url: "save_interfaceinfo",
            data: interfaceData,
            dataType: 'json',
            type: 'POST',
            beforeSend: function () {
                disableButtons($row);
                spinner.spin($row);
            },
            success: function () {
                clearChangedState($row);
                indicateSuccess($row);
                updateDefaults($row, interfaceData);
                // Restart the interface if a vlan change is done.
                if (interfaceData.hasOwnProperty('vlan')) {
                    restartInterface(interfaceData.interfaceid);
                }
            },
            error: function (jqXhr) {
                console.log(jqXhr.responseText);
                indicateError($row, $.parseJSON(jqXhr.responseText).messages);
            },
            complete: function (jqXhr) {
                removeFromQueue(rowid);
                enableButtons($row);
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

    function restartInterface(interfaceid) {
        /* Do a request to restart the interface with given id */
        $.post('restart_interface', {'interfaceid': interfaceid});
    }

    function disableButtons(row) {
        $(row).find('button').prop('disabled', true);
    }

    function enableButtons(row) {
        $(row).find('button').prop('disabled', false);
    }

    function indicateSuccess($row) {
        /* Highlight card to indicate success */
        removeAlerts($row);
        $row.addClass('success');
        setTimeout(function () {
            $row.removeClass('success');
        }, 1500);
    }

    function indicateError($row, messages) {
        var rowid = $row.prop('id'),
            $errorContainer = $('#' + rowid + '-errors');
        removeAlerts($errorContainer);
        for (var x = 0, l = messages.length; x < l; x++) {
            var $alertBox = $('<div>').addClass('alert-box alert').html(messages[x].message);
            $errorContainer.append($alertBox);
            $alertBox.click(function () {
                $(this).remove();
            });
        }
        $errorContainer.show();
    }

    function removeAlerts($container) {
        $container.find('.alert-box').remove();
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
        if ('ifadminstatus' in data) {
            updateAdminStatusDefault($row, data.ifadminstatus);
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

    function updateAdminStatusDefault($row, new_value) {
        var $adminStatusCheckbox = $row.find('.ifadminstatus');
        var old_value = $adminStatusCheckbox.attr('data-orig');
        if (old_value !== new_value) {
            $adminStatusCheckbox.attr('data-orig', new_value);
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


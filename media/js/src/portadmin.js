require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {

    if(!Array.indexOf){
        Array.prototype.indexOf = function(obj){
            for(var i=0; i<this.length; i++){
                if(this[i]==obj){
                    return i;
                }
            }
            return -1;
        }
    }
    var nav_ajax_queue = [];

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
        $(table).find('.vlanlist').on('change', function () {
            var $select = $(this);
            if ($select.val() == 'trunk') {
                location.href = $select.find(':selected').attr('data-url');
            }
        });
    }

    /*
     * When user changes either the textfield or the dropdown from it's
     * original value, mark the row as changed. If the change results in the
     * original value, mark the row as unchanged.
     */
    function addChangeListener(table) {
        $(table).find('tbody').on('change keyup keypress blur click', function (event) {
            var $target = $(event.target);
            var valid_classes = ['ifalias', 'vlanlist', 'voicevlan'];
            var classString = $target.attr('class');
            var classes = classString ? classString.split(' ') : [];
            for (var cls in classes) {
                if ($.inArray(cls, valid_classes)) {
                    var row = $target.parents('tr');
                    if (textFieldChanged(row) || dropDownChanged(row) || voiceVlanChanged(row)) {
                        markAsChanged(row);
                    } else {
                        markAsUnchanged(row);
                    }
                }
            }
        });
    }

    function addSaveListener(element) {
        $('.save', element).click(saveRow);
    }

    function addSaveAllListener(element) {
        $('.saveall_button').click(bulkSave);
    }

    function bulkSave() {
        $("tr.changed").each(saveRow);
    }

    /*
     * Undo the changes the user has done on the ifalias and vlan dropdown
     *
     * Consider: If the user has saved, update the undo information?
     */
    function addUndoListener(element) {
        $('.undo', element).click(function () {
            var row = $(this).parents('tr');
            var ifalias = $(row).find(".ifalias");
            var vlan = $(row).find(".vlanlist");
            $(ifalias).val($(ifalias).attr('data-orig'));
            $(vlan).val($('[data-orig]', vlan).val());
            clearChangedState(row);
        });
    }

    function addToggleVlanInfoListener(element) {
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
        return $(element).attr('data-orig') != $(element).val();
    }

    function dropDownChanged(row) {
        var dropdown = $(row).find(".vlanlist");
        var origOption = $('[data-orig]', dropdown)[0];
        var selectedOption = $('option:selected', dropdown)[0];
        return origOption != selectedOption;
    }

    function voiceVlanChanged(row) {
        var $checkbox = $(row).find('.voicevlan');
        var origOption = $checkbox.attr('data-orig');
        var checkedValue = $checkbox.prop('checked');
        // NB: Misusing == here
        return origOption != checkedValue;
    }

    function markAsChanged(row) {
        $(row).addClass("changed");
    }

    function markAsUnchanged(row) {
        $(row).removeClass("changed");
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
        var data = {};
        data['interfaceid'] = $row.prop('id');
        if (textFieldChanged($row)) {
            data['ifalias'] = $row.find(".ifalias").val();
        }
        if (dropDownChanged($row)) {
            data['vlan'] = $row.find(".vlanlist").val();
        }
        if (voiceVlanChanged($row)) {
            data['voicevlan'] = $row.find(".voicevlan").prop('checked');
        }
        return data;
    }

    function saveInterface($row, interfaceData) {
        console.log({'row': $row, 'data': interfaceData});

        var rowid = $row.prop('id');
        // If a save on this row is already in progress, do nothing.
        if (nav_ajax_queue.indexOf(rowid) > -1) {
            return;
        }
        disableSaveallButtons();
        nav_ajax_queue.push(rowid);

        $.ajax({url: "save_interfaceinfo",
            data: interfaceData,
            dataType: 'json',
            type: 'POST',
            beforeSend: function () {
                $('tr.error').remove();
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
                if (nav_ajax_queue.length == 0) {
                    enableSaveallButtons();
                }
            }
        });
    }

    function indicateSuccess($row) {
        /* Animate row to indicate success */
        var $cells = $row.find('td');

        $row.addClass('success');
        $cells.animate({'background-color': '#FFF'}, 3000, function () {
            $cells.removeAttr('style');
            $row.removeClass('success');
        });
    }

    function indicateError($row, messages) {
        var $newRow = $('<tr/>').addClass('error'),
            $cell = $('<td class="" colspan="10"/>'),
            $message = $('<span/>');

        var error = '';
        for (var x = 0, message; message = messages[x]; x++) {
            if (message.level === 40) {
                error += message.message + '. ';
            }
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
            updateIfAliasDefault($row, data['ifalias']);
        }
        if ('vlan' in data) {
            updateVlanDefault($row, data['vlan']);
        }
    }

    function updateIfAliasDefault($row, ifalias) {
        var old_ifalias = $row.find(".ifalias").attr('data-orig');
        if (old_ifalias !== ifalias) {
            console.log('Updating ifalias default from ' + old_ifalias + ' to ' + ifalias);
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

    function removeFromQueue(id) {
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


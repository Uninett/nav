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
    var queue = new Array();

    $(document).ready(function(){
        NAV.addGlobalAjaxHandlers();

        var interfaceTable = $('#portadmin-interfacecontainer');
        var infoBox = $('#infobox');

        if (interfaceTable.length) {
            addChangeListener(interfaceTable);
            addSaveListener(interfaceTable);
            addSaveAllListener(interfaceTable);
            addUndoListener(interfaceTable);
            addToggleVlanInfoListener(infoBox);
        }
    });

    function addChangeListener(element) {
        $('.ifalias, .vlanlist', element).on('change keyup keypress blur', function(){
            var row = $(this).parents("tr");
            if (textFieldChanged(row) || dropDownChanged(row)) {
                markAsChanged(row);
            } else {
                markAsUnchanged(row);
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

        // If a save on this row is already in progress, do nothing.
        if (queue.indexOf(rowid) > -1) {
            return;
        }

        disableSaveallButtons();
        queue.push(rowid);

        var ifalias = $row.find(".ifalias").val();
        var vlan = $row.find(".vlanlist").val();

        // Post data and wait for json-formatted returndata. Display status information to user
        saveInterface(ifalias, vlan, rowid, $row);
    }

    function saveInterface(ifalias, vlan, rowid, $row) {
        console.log({'row': $row, 'rowid': rowid, 'ifalias': ifalias, 'vlan': vlan});
        $.ajax({url: "save_interfaceinfo",
            data: {'ifalias': ifalias, 'vlan': vlan, 'interfaceid': rowid},
            dataType: 'json',
            type: 'POST',
            success: function (data) {
                clearChangedState($row);
                indicateSuccess($row);
            },
            error: function (jqXhr) {
                console.log(jqXhr.responseText);
                displayCallbackInfo($row, jqXhr.responseText);
            },
            complete: function (jqXhr) {
                removeFromQueue(rowid);
                if (queue.length == 0) {
                    enableSaveallButtons();
                }
            }
        });
    }

    function indicateSuccess($row) {
        /* Animate row to indicate success */
        $row.addClass('success');
        $row.find('td').animate({'background-color': '#FFF'}, 4000);
        $row.removeClass('success');
    }

    function removeFromQueue(id) {
        var index = queue.indexOf(id);
        if (index > -1) {
            queue.splice(index, 1);
        }
    }

    function disableSaveallButtons() {
        $("input.saveall_button").attr('disabled', 'disabled');
    }

    function enableSaveallButtons() {
        $("input.saveall_button").removeAttr('disabled');
    }


    function displayCallbackInfo(row, data) {
        // Create new element
        var div = $("<div></div>").addClass("saveinfo");
        $("<p />").appendTo(div);
        $("body").append(div);

        // Add click-listener to remove element
        $(div).click(function(){
            $(this).remove();
        });

        // Calculate and set position
        var pos = $(row).find("td:last").offset(); // pos of last cell in row
        var left = pos.left + 70;
        var top = pos.top - 1;
        $(div).css({ "left": left + "px", "top": top + "px" });

        // Add correct layout
        if (data.error) {
            $(div).addClass("error");
        } else {
            $(div).addClass("success");
        }

        // Set message and show element
        $(div).find("p").html(data.message);
        $(div).show();

        // Automatically remove success messages
        if (!data.error) {
            $(div).fadeOut(6000, function(){
                $(this).remove();
            });
        }
    }



});


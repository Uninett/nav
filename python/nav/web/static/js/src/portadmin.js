require(['libs/spin.min', 'libs/jquery-ui.min'], function (Spinner) {

    /**
     * Helper object to manipulate the modal and give feedback
     */
    function Feedbacker(modal) {
        this.modal = null;
        this.isOpen = false;
        this.list = null;
        this.closeButton = null;
    }

    Feedbacker.prototype = {
        modalOpen: async function() {
            if (this.isOpen) {
                return Promise.resolve();
            }
            return htmx.ajax('GET', '/portadmin/feedback_modal', {
                target: 'body',
                swap: 'beforeend'
            }).then(() => {
                this.modal = document.getElementById('portadmin-feedback-modal');
                this.list = this.modal.querySelector('ul');
                this.isOpen = true;
            })
        },
        modalClose: function() {
            this.modal.remove();
            this.closeButton.remove();
            this.isOpen = false;
            this.modal = null;
            this.list = null;
            this.closeButton = null;
        },
        addCloseButton: function() {
            const self = this;
            const button = document.createElement('button');
            button.className = 'button small';
            button.textContent = 'Close';
            button.style.marginBottom = '0';
            button.onclick = function() {
                self.modalClose();
            };
            this.modal.querySelector('.modal-content').appendChild(button);
            this.closeButton = button;
        },
        /**
         * The cancel button will empty the queue of interfaces to handle, but
         * the commit configuration request will still be sent.
         * NB: Currently not in use
         */
        addCancelButton: function() {
            var self = this;
            var $button = $('<button class="button secondary small pull-right">Cancel</button>');
            this.modal.append($button);
            $button.on('click', function() {
                emptyQueue();
                self.addFeedback('Jobs cancelled');
                $button.attr('disabled', true);
            });
            this.cancelButton = $button;
        },
        addFeedback: async function(text, status, message) {
            await this.modalOpen();
            const listItem = $('<li>').appendTo(this.list).html(text);
            if (typeof status !== 'undefined') {
                listItem.append(this.createAlert(status, message));
            }
            return listItem;
        },
        createAlert: function(status, message) {
            var alert = $('<span class="label" style="margin-left: 1em;">').attr('title', message);
            switch (status) {
            case 'success':
                alert.addClass(status).html('Ok');
                break;
            case 'alert':
                alert.addClass(status).html('Failed');
                break;
            }
            return alert;
        },
        createProgress: function() {
            return $('<progress style="margin-left: 1em; width: 50px; vertical-align: sub"></progress>');
        },
        savingInterface: function($row) {
            var self = this;
            return this.addFeedback('Configuring interface ' + $row.find('.port-name').text())
                .then(function(listItem) {
                    if (listItem) {
                        listItem.append(self.createProgress());
                    }
                    return listItem;
                });
        },
        restartingInterfaces: async function() {
            const restartReason = "A computer connected to a port does not detect that the vlan changes. When that happens the computer will have the IP-address from the old vlan and it will lose connectivity. But if the link goes down and up (a 'restart') the computer will send a request for a new address. 'Restarting' interfaces is only done when changing vlans.";
            const why = $('<span aria-describedby="restart-tooltip">(why?)</span>');
            why.on('click', () => {
                $('#restart-reason').toggleClass('hidden');
            })
            const listItem = await this.addFeedback('Restarting interfaces ');
            listItem.append(why, this.createProgress());
            const restartReasonElement = $(
                '<div id="restart-reason" class="hidden panel">' +
                '<small>' + restartReason + '</small' +
                '</div>'
            );
            listItem.append(restartReasonElement);
            return listItem;
        },
        committingConfig: function() {
            const self = this;
            return this.addFeedback('Committing configuration changes')
                .then(function(listItem) {
                    if (listItem) {
                        listItem.append(self.createProgress());
                    }
                    return listItem;
                });
        },
        endProgress: function(listItem, status, message) {
            status = typeof status === 'undefined' ? 'success' : status;
            message = typeof message === 'undefined' ? '' : message;

            const alertElement = this.createAlert(status);
            const progressElement = listItem.find('progress');
            progressElement.replaceWith(alertElement);

            if (status !== 'success') {
                const errorElement = $('<small style="margin-left: 1em">').text(message);
                errorElement.insertAfter(alertElement);
            }
        }
    };


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

    var restart_queue = [];  // Queue for interfaces that are restarting
    var nav_ajax_queue = [];  // Queue for cards we are saving
    var queue_data = {};  // Object containing data for ajax requests

    /* Mapping for ifadminstatus */
    var ifAdminStatusMapping = {
        1: true,
        2: false
    };

    /* Generic spinner created for display in the middle of a cell */
    // var spinner = new Spinner({length: 3, width: 2, radius: 5});
    var parentSelector = '.port_row';
    var feedback;

    $(document).ready(function(){
        feedback = new Feedbacker();

        // Initialize listeners after htmx has swapped in new content
        $(document).on("htmx:afterSwap", "#port-details", function() {
            var $wrapper = $('#portadmin-wrapper');

            if ($wrapper.length) {
                addTrunkSelectedListener($wrapper);
                addChangeListener($wrapper);
                addSaveListener($wrapper);
                addSaveAllListener($wrapper);
            }
        });
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
        $wrapper.on('change', '.poelist', function (event) {
            actOnChange($(event.target).parents(parentSelector));
        });
    }

    /*
     * Mark card changed or not based on values in card
     */
    function actOnChange(row) {
        if (textFieldChanged(row) || dropDownChanged(row) || voiceVlanChanged(row) || adminStatusChanged(row) || poeDropDownChanged(row)) {
            markAsChanged(row);
        } else {
            markAsUnchanged(row);
        }
    }

    function addSaveListener($wrapper) {
        /* Save when clicking on the save buttons. */
        $wrapper.on('click', '.changed .portadmin-save', async function (event) {
            var $row = $(event.target).parents(parentSelector);
            await saveRow($row);
        });
    }

    function addSaveAllListener(element) {
        $('.saveall_button').click(bulkSave);
    }

    function bulkSave() {
        $(".changed").each(async function (index, card) {
            await saveRow($(card));
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

    function poeDropDownChanged(row) {
        var dropdown = $(row).find(".poelist");
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

    async function saveRow($row) {
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
        await saveInterface(create_ajax_data($row));
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
        if (poeDropDownChanged($row)) {
            data.poe_state = $row.find(".poelist").val();
        }
        if ($row.find(".voicevlan").prop('checked')) {
            data.voice_activated = true;
        }
        return data;
    }

    async function saveInterface(interfaceData) {
        var rowid = interfaceData.interfaceid;
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

        await doAjaxRequest(rowid);
    }

    async function doAjaxRequest(rowid) {
        console.log('Saving interface with id ' + rowid);
        const $row = $('#' + rowid);
        const interfaceData = queue_data[rowid];

        let listItem = null;

        try {
            // Wait for the feedback modal to open and get the list item
            listItem = await feedback.savingInterface($row);
            const csrfToken = $('#save-changes-form input[name="csrfmiddlewaretoken"]').val();

            // Perform the AJAX request
            await $.ajax({
                url: "save_interfaceinfo",
                data: interfaceData,
                dataType: 'json',
                type: 'POST',
                beforeSend: function () {
                    disableButtons($row);
                },
                headers: {
                    'X-CSRFToken': csrfToken
                },
                success: function () {
                    clearChangedState($row);
                    updateDefaults($row, interfaceData);
                    feedback.endProgress(listItem);
                    // Restart the interface if a vlan change was made.
                    if (interfaceData.hasOwnProperty('vlan')) {
                        restart_queue.push(interfaceData.interfaceid);
                    }
                    $(document).trigger('nav-portadmin-ajax-success');
                },
                error: function (jqXhr) {
                    console.log(jqXhr.responseText);
                    var messages;
                    try {
                        messages = $.parseJSON(jqXhr.responseText).messages;
                    } catch (error) {
                        messages = [{'message': 'Error saving changes'}];
                    }
                    indicateError($row, messages);
                    feedback.endProgress(listItem, 'alert', messages.map(function(message){
                        return message['message'];
                    }).join(', '));
                }
            });

        } catch (error) {
            console.error('Error in doAjaxRequest:', error);
            // Handle any errors that occurred during the process
            feedback.endProgress(listItem, 'alert', 'An unexpected error occurred');
        } finally {
            // Always execute cleanup code
            removeFromQueue(rowid);
            enableButtons($row);

            if (nav_ajax_queue.length === 0) {
                enableSaveallButtons();
                await commitConfig(interfaceData.interfaceid);
            } else {
                // Process next entry in queue
                await doAjaxRequest(nav_ajax_queue[0]);
            }
        }
    }

    /**
     * Commits configuration changes and then link cycles / restarts all
     * interfaces that had their access VLAN changed.
     */
    async function commitConfig(interfaceid) {
        /** Do a request to commit changes to startup config */
        console.log('Sending commit configuration request');

        const status = await feedback.committingConfig();
        const csrfToken = $('#save-changes-form input[name="csrfmiddlewaretoken"]').val();
        const request = $.ajax({
            url: 'commit_configuration',
            type: 'POST',
            data: {'interfaceid': interfaceid},
            headers: {
                'X-CSRFToken': csrfToken
            },
        });
        request.done(function() {
            feedback.endProgress(status, 'success', request.responseText);
            restartInterfaces();
        });
        request.fail(function(err) {
            feedback.endProgress(status, 'alert', request.responseText);
            feedback.addCloseButton();
        });
    }

    async function restartInterfaces() {
        // Sends a request to restart all interfaces in the restart queue, if any, and then add
        if (restart_queue.length == 0) {
            feedback.addCloseButton();
            return;
        }

        const listItem = await feedback.restartingInterfaces();
        const request = $.post('restart_interfaces', {'interfaceid': restart_queue});
        request.done(function() {
            console.log("Interfaces restarted: " + restart_queue)
            feedback.endProgress(listItem, 'success');
        });
        request.fail(function() {
            console.log("Interfaces restarted: " + restart_queue)
            feedback.endProgress(listItem, "alert", request.responseText);
        });
        request.always(function() {
           restart_queue.length = 0;
            feedback.addCloseButton();
        });
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
        if ('poe_state' in data) {
            updatePoeDefault($row, data.poe_state);
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

    function updatePoeDefault($row, new_value) {
        var old_value = $row.find('option[data-orig]').val();
        if (old_value !== new_value) {
            console.log('Updating PoE state default from ' + old_value + ' to ' + new_value);
            $row.find('option[data-orig]').removeAttr('data-orig');
            $row.find('option[value=' + new_value + ']').attr('data-orig', new_value);
        }
    }

    function removeFromQueue(id) {
        if (queue_data.hasOwnProperty(id)) {
            delete queue_data[id];
        }
        var index = nav_ajax_queue.indexOf(id);
        if (index > -1) {
            nav_ajax_queue.splice(index, 1);
        }
    }

    function emptyQueue() {
        for(var prop in queue_data) {
            if (queue_data.hasOwnProperty(prop)) {
                delete queue_data[prop];
            }
        }
        nav_ajax_queue.splice(0, nav_ajax_queue.length);
    }

    function disableSaveallButtons() {
        $("input.saveall_button").attr('disabled', 'disabled');
    }

    function enableSaveallButtons() {
        $("input.saveall_button").removeAttr('disabled');
    }

    $(document).ready(function() {
        $(".toggle-all").click(function() {
            var $checkboxes = $(this).parents().find('input[type=checkbox]');
        $checkboxes.prop('checked', $(this).is(':checked'));
        });
    });

});

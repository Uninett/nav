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

    /* Generic spinner created for display in the middle of a cell */
    var spinner = new Spinner({length: 3, width: 2, radius: 5});


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
            actOnChange($(event.target).parents('.portadmin-card'));
        });
        $wrapper.on('change', '.vlanlist', function (event) {
            actOnChange($(event.target).parents('.portadmin-card'));
        });
        $wrapper.on('click', '.voicevlan', function (event) {
            actOnChange($(event.target).parents('.portadmin-card'));
        });
    }

    /*
     * Mark card changed or not based on values in card
     */
    function actOnChange(card) {
        if (textFieldChanged(card) || dropDownChanged(card) || voiceVlanChanged(card)) {
            markAsChanged(card);
        } else {
            markAsUnchanged(card);
        }
    }

    function addSaveListener($wrapper) {
        /* Save when clicking on the save buttons. */
        $wrapper.on('click', '.save-interface', function (event) {
            var $card = $(event.target).parents('.portadmin-card');
            saveRow($card);
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

    function textFieldChanged(card) {
        var element = $(card).find(".ifalias");
        return $(element).attr('data-orig') !== $(element).val();
    }

    function dropDownChanged(card) {
        var dropdown = $(card).find(".vlanlist");
        var origOption = $('[data-orig]', dropdown)[0];
        var selectedOption = $('option:selected', dropdown)[0];
        return origOption !== selectedOption;
    }

    function voiceVlanChanged(card) {
        /*
         * XOR checkbox checked and original value to see if changed
         */
        var $checkbox = $(card).find('.voicevlan');
        if ($checkbox.length) {
            var origOption = $checkbox.attr('data-orig').toLowerCase() === 'true';
            var checkedValue = $checkbox.prop('checked');
            return checkedValue ^ origOption;
        } else {
            return false;
        }
    }

    function markAsChanged(card) {
        var $card = $(card);
        if (!$card.hasClass('changed')) {
            $card.addClass("changed");
        }
    }

    function markAsUnchanged(card) {
        var $card = $(card);
        if ($card.hasClass('changed')) {
            $card.removeClass("changed");
        }
    }

    function clearChangedState(card) {
        markAsUnchanged(card);
    }

    function saveRow($card) {
        /*
         * This funcion does an ajax call to save the information given by the user
         * when the save-button is clicked.
         */

        var cardid = $card.prop('id');
        if (!cardid) {
            console.log('Could not find id of card ' + $card);
            return;
        }

        // Post data and wait for json-formatted returndata. Display status information to user
        saveCard($card, create_ajax_data($card));
    }

    function create_ajax_data($card) {
        /*
         Create the object used in the ajax call.
         */
        var data = {};
        data.interfaceid = $card.prop('id');
        if (textFieldChanged($card)) {
            data.ifalias = $card.find(".ifalias").val();
        }
        if (dropDownChanged($card)) {
            data.vlan = $card.find(".vlanlist").val();
        }
        if (voiceVlanChanged($card)) {
            data.voicevlan = $card.find(".voicevlan").prop('checked');
        }
        if ($card.find(".voicevlan").prop('checked')) {
            data.voice_activated = true;
        }
        return data;
    }

    function saveCard($card, interfaceData) {
        var cardid = $card.prop('id');
        // If a save on this card is already in progress, do nothing.
        if (nav_ajax_queue.indexOf(cardid) > -1) {
            return;
        }
        disableSaveallButtons();
        nav_ajax_queue.push(cardid);
        queue_data[cardid] = interfaceData;

        // Do not send more than one request at the time.
        if (nav_ajax_queue.length > 1) {
            return;
        }

        doAjaxRequest(cardid);
    }

    function doAjaxRequest(cardid) {
        var $card = $('#' + cardid);
        var interfaceData = queue_data[cardid];
        $.ajax({url: "save_interfaceinfo",
            data: interfaceData,
            dataType: 'json',
            type: 'POST',
            beforeSend: function () {
                $('tr.error').remove();
                disableButtons($card);
                spinner.spin($card);
            },
            success: function () {
                clearChangedState($card);
                indicateSuccess($card);
                updateDefaults($card, interfaceData);
            },
            error: function (jqXhr) {
                console.log(jqXhr.responseText);
                indicateError($card, $.parseJSON(jqXhr.responseText).messages);
            },
            complete: function (jqXhr) {
                removeFromQueue(cardid);
                enableButtons($card);
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

    function disableButtons(card) {
        $(card).find('button').prop('disabled', true);
    }

    function enableButtons(card) {
        $(card).find('button').prop('disabled', false);
    }

    function indicateSuccess($card) {
        /* Highlight card to indicate success */
        removeAlerts($card);
        $card.addClass('success');
        setTimeout(function () {
            $card.removeClass('success');
        }, 1500);
    }

    function indicateError($card, messages) {
        removeAlerts($card);
        for (var x = 0, l = messages.length; x < l; x++) {
            $card.append(
                $('<div class="alert-box alert"></div>').text(messages[x].message)
            );
        }
    }

    function removeAlerts($card) {
        $card.find('.alert-box').remove();
    }

    function updateDefaults($card, data) {
        if ('ifalias' in data) {
            updateIfAliasDefault($card, data.ifalias);
        }
        if ('vlan' in data) {
            updateVlanDefault($card, data.vlan);
        }
        if ('voicevlan' in data) {
            updateVoiceDefault($card, data.voicevlan);
        }
    }

    function updateIfAliasDefault($card, ifalias) {
        var old_ifalias = $card.find(".ifalias").attr('data-orig');
        if (old_ifalias !== ifalias) {
            $card.find(".ifalias").attr('data-orig', ifalias);
        }
    }

    function updateVlanDefault($card, vlan) {
        var old_vlan = $card.find('option[data-orig]').val();
        if (old_vlan !== vlan) {
            console.log('Updating vlan default from ' + old_vlan + ' to ' + vlan);
            $card.find('option[data-orig]').removeAttr('data-orig');
            $card.find('option[value=' + vlan + ']').attr('data-orig', vlan);
        }
    }

    function updateVoiceDefault($card, new_value) {
        var $voice_element = $card.find(".voicevlan");
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

});


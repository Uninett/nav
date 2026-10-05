/**
 * Matches all search terms when searching in Select2
 * Updated for Select2 v4 - matcher signature changed from (term, text) to (params, data)
 */
function select2MultipleMatcher(params, data) {
    // If there are no search terms, return all data
    if (!params.term || params.term.trim() === '') {
        return data;
    }
    // Check if text matches all search terms
    let has = true;
    const words = params.term.toUpperCase().split(" ");
    const text = data.text || '';
    words.forEach((word, idx) => {
        has = has && (text.toUpperCase().indexOf(word) >= 0);
    })
    // Return null if no match, or the data object if it matches
    return has ? data : null;
}

require([
    'plugins/csrf-utils',
    'plugins/rack_sensors'
], function (CsrfUtils, RackSensors) {

    const csrfToken = CsrfUtils.getCsrfToken();

    /**
     * TODO:
     * - How to set min and max values for the different sensors
     * - Naming - is it really racks?
     */


    /**
     * Applies listeners when modal for adding sensors is loaded
     * - form submit
     * - cancel click
     * - select2 component
     */
    function addSensorModalListeners($sensorModal) {
        document.body.addEventListener('htmx:afterSwap', function() {
            const $sensorModal = $('#add-sensor-modal');
            if (!$sensorModal.length) {
                return;
            }
            $sensorModal.find('#add-rackitem-tabs').tabs().show();
            const sumSelectClone = $sensorModal.find('.sumsensors').closest('label').clone();
            $sensorModal.find('.sensordropdown').select2({
                matcher: select2MultipleMatcher
            });
            $sensorModal.find('.sensordropdown').select2('open');

            $sensorModal.find('.sumform').on('change', '.sumsensors', function (event) {
                const label = $(event.target).closest('label');
                const clone = sumSelectClone.clone();
                clone.find('select').select2({
                    matcher: select2MultipleMatcher
                });
                label.after(clone);
            });
            $sensorModal.find('.cancelbutton').on('click', function (event) {
                event.preventDefault();
                $sensorModal.remove();
            });
        });

        document.body.addEventListener('room.rack.added', function () {
            $('[data-id="no-racks-alert"]').remove()
        })

        /* Form submission is handled by htmx, we just need to add a listener for
           when the sensor is added to update it with data */
        document.body.addEventListener('room.rack.sensorAdded', function(event) {
            const { rackId, sensorId } = event.detail;
            // Use a small delay to ensure HTMX swap is complete
            setTimeout(() => {
                const $sensor = $(`#item_${rackId}_${sensorId}`);
                if ($sensor.length) {
                    RackSensors.updateSingleSensor($sensor);
                }
            }, 100);
        });
    }


    /**
     * Updates all racks
     */
    function updateRacks() {
        $('.rack').each(function () {
            RackSensors.updateRack(this);
        });
    }


    /**
     * Listener for removing sensors
     */
    function addSensorRemoveListener() {
        $('#racks').on('click', '.remove-sensor', function () {
            const rackSensor = $(this).closest('.rack-sensor');
            const rack = $(this).closest('.rack');
            const request = $.ajax({
                url: NAV.urls.remove_sensor,
                type: 'POST',
                data: {
                    id: rackSensor.data('id'),
                    column: rackSensor.data('column'),
                    rackid: rack.data('rackid')
                },
                headers: {'X-CSRFToken': csrfToken}
            });
            request.done(function () {
                rackSensor.remove();
            });
        });
    }


    /**
     * Listener for removing racks
     */
    function addRackRemoveListener() {
        $('#racks').on('click', '.remove-rack', function (event) {
            // event.preventDefault();
            const yes = confirm('Really remove this rack?');
            if (yes) {
                const rack = $(this).closest('.rack');
                const request = $.ajax({
                    url: NAV.urls.remove_rack,
                    type: 'POST',
                    data: {rackid: rack.data('rackid')},
                    headers: {'X-CSRFToken': csrfToken}
                });
                request.done(function () {
                    rack.remove();
                });
            }
        });
    }


    /**
     * Add listeners for displaying and hiding edit mode
     */
    function addEditModeListener() {
        var $racks = $('#racks');

        function switchMode(func) {
            var $this = $(this);
            var $rack = $this.closest('.rack');
            $rack[func]('editmode');
        }

        $racks.on('click', '.edit-rack', function() {
            switchMode.call(this, 'addClass');
        });

        $racks.on('click', '.close-edit-rack', function() {
            switchMode.call(this, 'removeClass');
        });
    }


    // Toggle editmode on for empty racks
    function toggleEditEmptyRack() {
        $('.rack').each(function () {
            var $rack = $(this);
            if (!$rack.find('.rack-sensor').length) {
                $rack.find('.edit-rack').click();
            }
        });
    }


    function addRenameRackListener() {
        $('#racks').on('submit', '.rename-rack-form', function(event) {
            event.preventDefault();
            const $form = $(this);
            const request = $.ajax({
                url: $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                headers: {'X-CSRFToken': csrfToken}
            });
            request.fail(function () {
                console.log("Failed to rename rack");
            });
            request.done(function (name) {
                // Give a little flash to indicate success
                var $submit = $form.find('[type="submit"]');
                $submit.addClass('success');
                setTimeout(function () {
                    $submit.removeClass('success');
                }, 1000);
                $form.siblings('.rack-heading').find('.rackname').text(name);
            });
        });
    }


    function addSensorSort() {
        $('.rack').find('.rack-column .sensors').each(function() {
            $(this).sortable({
                tolerance: 'pointer',
                handle: '.fa-arrows',
                forcePlaceholderSize: true,
                placeholder: 'highlight',
                update: function(event, ui) {
                    var serialized = $(this).sortable('serialize', {
                        attribute: 'data-sortid'
                    });
                    var rack = $(this).closest('.rack');
                    var column = $(this).data('column');
                    serialized += '&column=' + column;
                    serialized += '&rackid=' + rack.data('rackid');
                    $.ajax({
                        url: NAV.urls.save_sensor_order,
                        type: 'POST',
                        data: serialized,
                        headers: {'X-CSRFToken': csrfToken}
                    });
                }
            });
        });
    }


    function addRackSort() {
        $('#racks-container').sortable({
            tolerance: 'pointer',
            handle: '.icon-container .fa-arrows',
            forcePlaceholderSize: true,
            placeholder: 'highlight',
            update: function (event, ui) {
                const serialized = $(this).sortable('serialize');
                $.ajax({
                    url: NAV.urls.save_rack_order,
                    type: 'POST',
                    data: serialized,
                    headers: {'X-CSRFToken': csrfToken}
                });
            }
        });
    }


    function addColorChooser() {
        $('#racks-container').on('change', 'form.color-chooser', function(event) {
            var classes = Array.from(this.querySelectorAll("input[type=radio]"), function(element) {
                return element.value;
            }).join(' ');

            var $radio = $(event.target),
                html_class = $radio.val(),
                rackid = $radio.closest('.rack').data('rackid');

            $.ajax({
                url: NAV.urls.save_rack_color,
                type: 'POST',
                data: {
                    rackid: rackid,
                    class: html_class
                },
                headers: {'X-CSRFToken': csrfToken}
            }).done(function() {
                $radio.closest('.rack').find('.rack-body').removeClass(classes).addClass(html_class);
            }).fail(function() {
                console.error('Failed updating html class');
            });
        });
    }


    /**
     * Runs on page load. Setup page
     */
    $(function () {

        // Add listener to edit-button, toggle edit-mode for empty racks
        addEditModeListener();
        toggleEditEmptyRack();

        addSensorModalListeners();

        addRackRemoveListener();
        addSensorRemoveListener();

        addRenameRackListener();

        addRackSort();
        addSensorSort();

        addColorChooser();

        // Start updating racks with data
        updateRacks();
        setInterval(updateRacks, 60000);

    });

});

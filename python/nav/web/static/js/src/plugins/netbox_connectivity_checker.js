define(['libs/spin.min'], function (Spinner) {

    /**
     * This plugin is only useful on the SeedDB add/edit netbox form.
     *
     * Should fill "Collected info" with values from hidden form elements
     * at page load.
     *
     * When button is clicked, sends a request for the read only data. If
     * the request is successful, "Collected info" is repopulated in addition
     * to the hidden elements. If not successful, an error message is
     * displayed.
     *
     */

    function Checker(ipchecker) {
        var form = $('#seeddb-netbox-form'),
            button = form.find('.check_connectivity');

        var errorAlertBox = createAlertBox('alert'),
            successAlertBox = createAlertBox('success');

        var spinContainer = $('<span>&nbsp;</span>').css({ position: 'relative', left: '20px'}).insertAfter(button),
            spinner = new Spinner({ 'width': 3, length: 8, radius: 5, lines: 11 });

        /**
         * Fake nodes are the ones displayed to the user. Real nodes are the
         * ones the form posts.
         */
        var fakeSysnameNode = $('<label>Sysname<input type="text" disabled></label>'),
            fakeTypeNode = $('<label>Type<input type="text" disabled></label>'),
            realSysnameNode = $('#id_sysname'),
            realTypeNode = $('#id_type');

        $('#real_collected_fields').after(fakeSysnameNode, fakeTypeNode);

        setDefaultValues();

        button.on('click', function () {
            hideAlertBoxes();
            var ip_address = $('#id_ip').val().trim();
            var profiles = []
            $.each($("#id_profiles option:selected"), function(){
                profiles.push($(this).val());
            });

            if (!(ip_address && profiles.length)) {
                var message = "We need an IP-address and at least one management profile to talk to the device.";
                reportError(message);
                return;
            }

            spinner.spin(spinContainer.get(0));
            disableForm();

            var checkHostname = ipchecker.getAddresses();
            checkHostname.done(function () {
                if (ipchecker.isSingleAddress) {
                    checkConnectivity(ip_address, profiles);
                } else {
                    onStop();
                }
            });

        });

        function checkConnectivity(ip_address, profiles) {
            console.log('Checking connectivity');
            var request = $.getJSON(NAV.urls.get_readonly, {
                'ip_address': ip_address,
                'profiles': profiles,
            });
            request.done(onSuccess);
            request.error(onError);
            request.always(onStop);
        }

        function disableForm() {
            form.css({'opacity': '0.5', 'pointer-events': 'none'});
        }

        function enableForm() {
            form.css({'opacity': 'initial', 'pointer-events': 'initial'});
        }

        function createAlertBox(addClass) {
            var alertBox = $('<div class="alert-box"><ul></ul></div>').hide().insertAfter(button);
            alertBox.reset = function() {
                $(this).hide();
                $(this).html('<ul></ul>');
            }
            alertBox.on('click', function () {
                alertBox.reset();
            });
            alertBox.addClass(addClass);
            return alertBox;
        }

        function setDefaultValues() {
            fakeSysnameNode.find('input').val(realSysnameNode.val());
            fakeTypeNode.find('input').val(realTypeNode.find('option:selected').html());
        }

        function setNewValues(data) {
            realSysnameNode.val(data.sysname);
            fakeSysnameNode.find('input').val(data.sysname);
            realTypeNode.val(data.netbox_type);
            fakeTypeNode.find('input').val(realTypeNode.find('option:selected').html());
            $('#id_serial').val(data.serial);
        }

        function reportErrorWithDetails(profile) {
            var profile_link = profile.name;
            if (profile.url) {
                profile_link = '<a href="' + profile.url + '" title="View profile details" onclick="event.stopPropagation();">' + profile_link + '</a>'
            }
            var failText = '<div><em>' + profile_link + '</em> failed'
            if (profile.custom_error === 'UnicodeDecodeError') {
                failText += ', perhaps because of non-ASCII characters in the sysLocation field.';
                failText += '<br><br>sysLocation: ' + profile.syslocation;
            }
            failText += '.</div>';
            failText += '<div><br>Error message: ' + profile.error_message + '</div>';
            reportError(failText);
        }

        function onSuccess(data) {
            if (data.profiles) {
                var profile_ids = Object.keys(data.profiles);
                profile_ids.forEach(function(profile_id) {
                    var profile = data.profiles[profile_id];

                    if (profile.status) {
                        reportSuccess('<em>' + profile.name + '</em>: <strong>OK</strong>');
                    } else {
                        reportErrorWithDetails(profile);
                    }
                    setNewValues(data);
                });
            } else {
                reportError('NAV backend response was incomplete');
            }

        }

        function onError() {
            reportError('Error during SNMP-request');
        }

        function onStop() {
            spinner.stop();
            enableForm();
        }

        function reportError(text) {
            errorAlertBox.contents("ul").append('<li>' + text + '</li>');
            errorAlertBox.show();
        }

        function reportSuccess(text) {
            successAlertBox.contents("ul").append('<li>' + text + '</li>');
            successAlertBox.show();
        }

        function hideAlertBoxes() {
            errorAlertBox.reset();
            successAlertBox.reset();
        }

    }

    return Checker;

});

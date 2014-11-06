define(['libs/jquery'], function () {

    /** This plugin is only useful on the SeedDB add/edit netbox form */

    function Checker() {
        console.log('ConnectivityCheckerForNetboxes called');

        var button = $('#seeddb-netbox-form').find('.check_connectivity');
        var alertBox = $('<div class="alert-box"></div>').hide().insertAfter(button);
        var spinContainer = $('<span>&nbsp;</span>').css({ position: 'relative', left: '20px'}).insertAfter(button);
        var spinner = new Spinner();

        var fakeSysnameNode = $('<label>Sysname<input type="text" disabled></label>'),
            fakeSnmpVersionNode = $('<label>Snmp version<input type="text" disabled></label>'),
            fakeTypeNode = $('<label>Type<input type="text" disabled></label>'),
            realSysnameNode = $('#id_sysname'),
            realSnmpVersionNode = $('#id_snmp_version'),
            realTypeNode = $('#id_type');

        $('#div_id_serial').before(fakeSysnameNode).before(fakeSnmpVersionNode).before(fakeTypeNode);

        setDefaultValues();

        button.on('click', function () {
            var ip_address = $('#id_ip').val().trim(),
                read_community = $('#id_read_only').val();

            if (!(ip_address && read_community)) {
                reportError('We need an IP-address and a community to talk to the device.');
                return;
            }

            alertBox.hide();
            spinner.spin(spinContainer.get(0));

            var request = $.getJSON(NAV.urls.get_readonly, {
                'ip_address': ip_address,
                'read_community': read_community
            });
            request.done(onSuccess);
            request.error(onError);
            request.always(onStop);
        });

        function setDefaultValues() {
            fakeSysnameNode.find('input').val(realSysnameNode.val());
            fakeSnmpVersionNode.find('input').val(realSnmpVersionNode.val());
            fakeTypeNode.find('input').val(realTypeNode.find('option:selected').html());
        }

        function onSuccess(data) {
            if (data.snmp_version) {
                reportSuccess('IP Device answered');
                realSysnameNode.val(data.sysname);
                fakeSysnameNode.find('input').val(data.sysname);
                realSnmpVersionNode.val(data.snmp_version);
                fakeSnmpVersionNode.find('input').val(data.snmp_version);
                realTypeNode.val(data.netbox_type);
                fakeTypeNode.find('input').val(realTypeNode.find('option:selected').html());
                $('#id_serial').val(data.serial);
            } else {
                reportError('IP Device did not answer. Is community correct?');
            }

        }

        function onError() {
            reportError('Error during SNMP-request');
        }

        function onStop() {
            spinner.stop();
        }

        function reportError(text) {
            alertBox.addClass('alert').removeClass('success').html(text).show();
        }

        function reportSuccess(text) {
            alertBox.addClass('success').removeClass('alert').html(text).show();
        }

    }

    return Checker;

});

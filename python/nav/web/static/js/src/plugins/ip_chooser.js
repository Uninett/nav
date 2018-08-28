define([], function () {

    /**
     * Plugin for choosing IP addresses if there are more than one result of a
     * lookup.
     *
     * Used in SeedDB - IP Device tab
     */

    function IpChooser(feedbackElement, addressField) {
        this.feedbackElement = feedbackElement;
        this.addressField = addressField;

        this.isSingleAddress = false;

        this.createDom();

        var self = this;
        this.list.on('change', function () {
            self.addressField.val(self.list.val());
        });
    }

    IpChooser.prototype = {
        createDom: function () {
            this.feedbackElement.hide();
            this.alertBox = $('<div class="alert-box alert"></div>');
            this.feedback = $('<span>');
            this.label = $('<label>').text('Please choose an IP address');
            this.list = $('<select>');

            this.feedbackElement.append(this.alertBox);
            this.alertBox.append(this.feedback).append(this.label);
            this.label.append(this.list);
        },

        getAddresses: function () {
            var address = this.addressField.val();
            var self = this;

            if (!address) {
                return;
            }

            this.feedbackElement.hide();

            var request = $.getJSON(
                NAV.urls.seeddb.verifyAddress,
                {'address': address}
            );

            request.done(function (data) {
                var addresses = data.addresses;
                if (addresses && addresses.length > 1) {
                    self.display(address, addresses);
                    self.isSingleAddress = false;
                } else {
                    self.isSingleAddress = true;
                }
            });

            return request;

        },

        display: function (address, addresses) {
            this.feedback.html('The hostname &quot;' + address +
                '&quot; resolves to multiple IP addresses.');
            this.list.empty();
            this.list.append($('<option value="">---------</option>'));

            for (var i = 0; i < addresses.length; i++) {
                var obj = addresses[i];
                this.list.append($('<option value="'+obj+'">'+obj+'</option>'));
            }

            this.feedbackElement.show();
        }
    };

    return IpChooser;

});

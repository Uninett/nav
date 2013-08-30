define(['libs/jquery'], function () {

    function DateUtils() {
//        this.node = (typeof(node) === 'string') ? $(node) : node;
    }

    DateUtils.prototype = {
        timeSince: function (now, then) {
            if (then > now) {
                var temp = now;
                now = then;
                then = temp;
            }
            var one_second = 1000;
            var one_minute = one_second * 60;
            var one_hour = one_minute * 60;
            var one_day = one_hour * 24;
            var difference = now - then;

            var days = parseInt(difference / one_day, 10);
            difference -= days * one_day;
            var hours = parseInt(difference / one_hour, 10);
            difference -= hours * one_hour;
            var minutes = parseInt(difference / one_minute, 10);
            difference -= minutes * one_minute;
            var seconds = parseInt(difference / one_second, 10);

            var timestamp = [hours, this.zeropad(minutes), this.zeropad(seconds)].join(':');
            var trail = " ago";

            if (days > 0) {
                return days + " days, " + timestamp + trail;
            } else {
                return timestamp + trail;
            }
        },
        zeropad: function (number) {
            return number < 10 ? '0' + String(number) : String(number);
        }
    };

    return DateUtils;

});

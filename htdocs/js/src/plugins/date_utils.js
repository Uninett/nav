define(['libs/jquery'], function () {

    function DateUtils() {
//        this.node = (typeof(node) === 'string') ? $(node) : node;
    }

    DateUtils.prototype = {
        addHoverTimeSince: function (nodeSelector) {
            var that = this;
            $(nodeSelector).each(function (index, node) {
                $(node).mouseover(function () {
                    try {
                        var text = $(this).text();
                        var date = new Date(text);
                        $(this).attr('data-timestamp', text);
                        $(this).text(that.timeSince(new Date(), date));
                    } catch(error) {
                        // do nothing
                    }
                });
                $(node).mouseout(function (index, node) {
                    try {
                        $(this).text($(this).attr('data-timestamp'));
                        $(this).removeAttr('data-timestamp');
                    } catch(error) {
                        // we're happy
                    }
                });
            })
        },
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

            var days = parseInt(difference / one_day);
            difference -= days * one_day;
            var hours = parseInt(difference / one_hour);
            difference -= hours * one_hour;
            var minutes = parseInt(difference / one_minute);
            difference -= minutes * one_minute;
            var seconds = parseInt(difference / one_second);

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

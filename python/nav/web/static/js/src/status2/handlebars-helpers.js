require(['moment', 'libs/handlebars'], function (moment, Handlebars) {

    //  format an ISO date using Moment.js
    //  http://momentjs.com/
    //  moment syntax example: moment(Date("2011-07-18T15:50:52")).format("MMMM YYYY")
    //  usage: {{dateFormat creation_date format="MMMM YYYY"}}
    // Credits: https://gist.github.com/stephentcannon/3409103
    Handlebars.registerHelper('dateFormat', function(context, block) {
        var today = moment(),
            date = moment(context),
            defaultFormat = 'DD.MMM HH:mm:ss';

        if (!today.isSame(date, 'year')) {
            defaultFormat = "YYYY-MM-DD HH:mm:ss";
        } else if (today.isSame(date, 'day')) {
            defaultFormat = 'HH:mm:ss';
        }
        var f = block.hash.format || defaultFormat;
        return date.format(f);
    });

    Handlebars.registerHelper('timeSince', function(context) {
        var date = moment(context);
        return date.fromNow(true);
    });
});

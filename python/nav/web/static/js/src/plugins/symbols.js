define(function (require) {

    var map = {
        'ampere': 'A',
        'celsius': '&#176;'
    };

    function symbol(unit) {
        unit = unit.toLowerCase();
        return map[unit] ? map[unit] : '';
    }

    return symbol;

});

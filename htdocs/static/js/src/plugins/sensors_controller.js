define([
    "libs-amd/text!resources/room/sensor.html",
    "libs-amd/text!resources/room/detail.html",
    "libs-amd/text!resources/room/counter.html",
    "plugins/sensor_controller"],
function (sensorTemplate, detailTemplate, counterTemplate, SensorController) {

    function SensorsController($sensors) {
        var templates = {
            'sensorTemplate': Handlebars.compile(sensorTemplate),
            'detailsTemplate': Handlebars.compile(detailTemplate),
            'counterTemplate': Handlebars.compile(counterTemplate)
        };

        $sensors.each(function (index, element) {
            new SensorController($(element), templates);
        });
    }

    return SensorsController;

});

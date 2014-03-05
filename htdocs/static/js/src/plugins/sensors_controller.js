define([
    "libs-amd/text!resources/room/sensor.html",
    "libs-amd/text!resources/room/detail.html",
    "plugins/sensor_controller"],
function (sensorTemplate, detailTemplate, SensorController) {

    function SensorsController($sensors) {
        var templates = {
            'sensorTemplate': Handlebars.compile(sensorTemplate),
            'detailsTemplate': Handlebars.compile(detailTemplate)
        };

        $sensors.each(function (index, element) {
            new SensorController($(element), templates);
        });
    }

    return SensorsController;

});

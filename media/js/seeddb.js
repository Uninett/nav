$(function() {
    var c = $("#toggle_checkbox").attr("checked");
    var checked = true;
    if (c == undefined) {
        checked = false;
    }
    $("#select").append('<input type="checkbox" id="toggle_checbox" />');
    $("#toggle_checbox").click(function() {
        if (checked) {
            $(".selector").removeAttr("checked");
        } else {
            $(".selector").attr("checked", "checked");
        }
        checked = !checked;
    });
});

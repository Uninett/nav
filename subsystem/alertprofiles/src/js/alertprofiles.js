$(function() {
	$("tr.all").hover(function () {
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).addClass('hilight');
	}, function() {
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).removeClass('hilight');
	});
});

$("select#id_operator").ready(function() {
    if ($(this).val() == 0) {
        $("select#id_value").removeAttr('multiple');
    }

    $("select#id_operator").change(function() {
        if ($(this).val() == 0) {
            $("select#id_value").removeAttr('multiple');
        } else {
            $("select#id_value").attr('multiple', 'multiple');
        }
    });
});

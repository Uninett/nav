$(function() {
	$("tr.all").hover(function () {
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).addClass('hilight');
	}, function() {
		var shared_id = $(this).attr('class').split(' ').slice(-1);
		$("tr." + shared_id).removeClass('hilight');
	});
});


require(["jquery"], function () {

	$(function () {

		var toggleTraceback = function () {
			$('#chevron').toggleClass('fa-chevron-up');
			$('#chevron').toggleClass('fa-chevron-down');
			$('.traceback-info').toggle();
		}

		$('#traceback').on('click', function (e) {
			e.preventDefault();
			toggleTraceback();
		});
	});

});

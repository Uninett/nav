/**
	JavaScript functions for NetworkExplorer
**/

$(document).ready(
	function() {
		$('#working').css('visibility', 'hidden');
	}
);

/* Search-handler  */

$(function(){
	// Catch the submit action
	$('#searchForm').submit(function(){
		// Get all the parameters we can get from the form
		var parameters = {};
		$(':input', this).each(
			function(){
				parameters[this.name] = escape($(this).val());
			});

	$('#searchForm').fadeTo("normal", 0.25);
	var moved = false;

	$.getJSON('/networkexplorer/search', parameters,
		function(data){

		var num_routers = data.routers.length;
		var num_gwports = data.gwports.length;
		var num_swports = data.swports.length;

        if (num_routers == 0){
            $('#search').css('background-color', '#cc0000');
		    $('#searchForm').fadeTo(2000, 1.0, function(){
                $('#search').css('background-color', '#ffffff');
                });
            return;
        }

		// We dont want to bring the server down by requesting to much in parallel
		$.ajaxSetup({
				  async: false
		});

		//
		// Process all the router matches
		//
		$.each(data.routers,
			function(i, _router){

				var router = $('#router-' + _router[0]);
				var data_node = $(router.children().select('img')).parent('dd');
				var data = _router[1];

				// Show off the result
				router.css('font-weigth', 'bold');

				// Append the data under the router-node
				data_node.append(data);

				// We make sure we dont ask for this node from the server again
				data_node.data("loaded", "true");

				// Show the children of the node
				data_node.children().select("dl").not("img").show();

				// Change tree-icon to collapsed
				$(router.children().select("img[src$='expand.gif']")).attr('src', '/images/networkexplorer/collapse.gif');

				// If we only have router-matches, we move to first result
				if (!moved && num_gwports == 0){
					document.location = '#router-' + _router[0];
					moved = true;
				}
			});
		//
		// Process all the gwport matches
		//
		$.each(data.gwports,
			function(i, _gwport){

		 		var gwport = $('#gwport-' + _gwport[0]);
				var data_node = $(gwport.children().select('img')).parent('dd');
				var data = _gwport[1];

				// Show off the search result
				gwport.addClass('highlight');

				// Append the data under the gwport-node
				data_node.append(data);

				// We dont want to load this node again from the server
				data_node.data("loaded","true");

				// Show the newly added children
				data_node.children().select("dl").not("img").show();

				// Set the tree-icon
				$(data_node.children().select("img[src$='expand.gif']")).attr('src', '/images/networkexplorer/collapse.gif');

				// If we gwport-matches, we move to first result
				if (!moved && num_swports == 0){
					document.location = '#gwport-' + _gwport[0];
					moved = true;
				}
			});

		//
		// Process all the swport matches
		//
		$.each(data.swports,
			function(i, _swport){

				var swport = $('#swport-' + _swport[0]);
				var data_node = $(swport.children().select('img').parent('dd'));
				var data = _swport[1];

				swport.addClass('highlight');
				swport.children().addClass('service_match'); // TODO: Misleading name

				data_node.append(data);
				data_node.data("loaded", "true");
				data_node.children().select("dl").not("img").show();

				$(data_node.children().select("img[src$='expand.gif']")).attr('src', '/images/networkexplorer/collapse.gif');

				if (!moved){
					document.location = '#swport-' + _swport[0];
					moved = true;
				}
			});

		// Done parsing all data.
		$('#searchForm').fadeTo("normal", 1.0);

		});


		return false;
	});
});

function openNode(img){
	var expand_type = $(img).parent().attr('id').substr(0,6);
	var expand_id   = $(img).parent().attr('id').substr(7);

	// Check if we are expanding a vlan on a switch
	var vlans = $(img).parent('dd').children("a[name^='switch-']").attr("name");
	if (vlans != null) {

		expand_type = 'switch';
		var values = vlans.split("-");
		expand_id = values[1];
		var vlan_id = values[2];
	}

	// We dont want to double-load data and such,
	// so we set/check a state for that tree-node
	if ($(img).parent('dd').data('working') == "true"){
		return false;
	} else {
		$(img).parent('dd').data('working', 'true');
	}

	if ($(img).parent('dd').data("loaded") == "true"){
		$(img).parent('dd').data('working', 'false');
		$(img).parent('dd').children().select("dl").not("img").not("a").not('abbr').slideToggle("fast",
	function () {

		if ($(img).parent('dd').children().select("dl").not("img").css('display') == 'block'){ 
					$(img).attr('src', '/images/networkexplorer/collapse.gif');
			} else {
					$(img).attr('src', '/images/networkexplorer/expand.gif');
			}
	});

		return false;
	}

	$(img).attr('src', '/images/main/process-working.gif');
	// We want to show/hide nodes when we actually have any data to show/hide
	$(img).parent('dd').ajaxSuccess(
		function(){
			$(img).parent('dd').data('working', "false");
		});

	if (expand_type == "router"){
		$.get('/networkexplorer/expand/router',
			{ 'netboxid': expand_id },
			function(data){
				$(img).parent('dd').append(data);
				$(img).parent('dd').data("loaded", "true");
				$(img).attr('src', '/images/networkexplorer/collapse.gif');
			});
	}
	if (expand_type == "switch"){
		$.get('/networkexplorer/expand/switch',
			{ 'netboxid': expand_id, 'vlanid': vlan_id },
			function(data){
				$(img).parent('dd').append(data);
				$(img).parent('dd').data("loaded", "true");
				$(img).attr('src', '/images/networkexplorer/collapse.gif');
			});
	}
	if (expand_type == "gwport"){
		$.get('/networkexplorer/expand/gwport',
			{ 'gwportid': expand_id },
			function(data){
				$(img).parent('dd').append(data);
				$(img).parent('dd').data("loaded", "true");
				$(img).attr('src', '/images/networkexplorer/collapse.gif');
			});
	}
	if (expand_type == "swport"){
		$.get('/networkexplorer/expand/swport',
			{ 'swportid': expand_id },
			function(data){
				$(img).parent('dd').append(data);
				$(img).parent('dd').data("loaded", "true");
				$(img).attr('src', '/images/networkexplorer/collapse.gif');
			});
	}
};


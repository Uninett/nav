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
	$(':input', this).each(function(){
            if (this.type == "checkbox"){
                if (this.checked){
		    console.debug(this.checked);
                    parameters[this.name] = "on";
                } else {
                    parameters[this.name] = "off";
                }
            } else {
                parameters[this.name] = escape($(this).val());
            }
	});

	$('#searchForm').fadeTo("normal", 0.25);

	$.ajax({
	    url: '/networkexplorer/search',
	    dataType: 'json',
	    data: parameters,
	    beforeSend: before_send,
	    error: request_error,
	    success: parse_result
	});

	return false;
    });
});


function before_send() {
    $('#navbody span.info').remove();
}

function request_error() {
    fade_to_normal();
    inform_user('An error occured during search');
}

function visualize_not_found() {
    fade_to_normal();
    inform_user('Search result was empty');
}

function inform_user(text) {
    var infonode = $('<span class="info" />');
    infonode.text(text);
    $('#searchForm').after(infonode);
}

function fade_to_normal() {
    $('#searchForm').fadeTo("normal", 1.0);
}

function parse_result(data) {
    if (data.routers.length == 0){
	visualize_not_found();
	return;
    }

    // We dont want to bring the server down by requesting to much in parallel
    $.ajaxSetup({
	async: false
    });

    // Process all the router matches
    $.each(data.routers, process_router);

    // Process all the gwport matches
    $.each(data.gwports, process_gwport);

    // Process all the swport matches
    $.each(data.swports, process_swport);

    scroll_to_result(data.routers, data.gwports, data.swports);

    // Done parsing all data.
    fade_to_normal();
}

function scroll_to_result(routers, gwports, swports) {
    if (swports.length > 0) {
	document.location = '#swport-' + swports[0][0];
    } else if (gwports.length > 0) {
	document.location = '#gwport-' + gwports[0][0];
    } else if (routers.length > 0) {
	document.location = '#router-' + routers[0][0];
    }
}

function process_router(i, _router){
    var router = $('#router-' + _router[0]);
    var data = _router[1];

    router.css('font-weigth', 'bold');
    append_data(router, data);
    switch_icon(router);
}

function process_gwport(i, _gwport){
    var gwport = $('#gwport-' + _gwport[0]);
    var data = _gwport[1];

    gwport.addClass('highlight');
    append_data(gwport, data);
    switch_icon(gwport);
}

function process_swport(i, _swport){
    var swport = $('#swport-' + _swport[0]);
    var data = _swport[1];

    swport.addClass('highlight');
    swport.children().addClass('service_match'); // TODO: Misleading name
    append_data(swport, data);
    switch_icon(swport);
}

function append_data(data_node, data) {
    // Append the data to the node
    data_node.append(data);

    // We dont want to load this node again from the server
    data_node.data("loaded","true");

    // Show the newly added children
    data_node.children().select("dl").not("img").show();
}


// Change tree-icon to collapsed
function switch_icon(node) {
    var collapseImage = NAV.imagePath + '/images/networkexplorer/collapse.gif';
    $(node.children().select("img[src$='expand.gif']")).attr('src', collapseImage);
}


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
            if ($(img).parent('dd').children().select("dl").not("img").css('display') == 'block') {
                $(img).attr('src', NAV.imagePath + '/images/networkexplorer/collapse.gif');
            } else {
                $(img).attr('src', NAV.imagePath + '/images/networkexplorer/expand.gif');
            }
        });

        return false;
    }

    $(img).attr('src', NAV.imagePath + '/images/main/process-working.gif');
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
		  $(img).attr('src', NAV.imagePath + '/images/networkexplorer/collapse.gif');
	      });
    }
    if (expand_type == "switch"){
	$.get('/networkexplorer/expand/switch',
	      { 'netboxid': expand_id, 'vlanid': vlan_id },
	      function(data){
		  $(img).parent('dd').append(data);
		  $(img).parent('dd').data("loaded", "true");
		  $(img).attr('src', NAV.imagePath + '/images/networkexplorer/collapse.gif');
	      });
    }
    if (expand_type == "gwport"){
	$.get('/networkexplorer/expand/gwport',
	      { 'gwportid': expand_id },
	      function(data){
		  $(img).parent('dd').append(data);
		  $(img).parent('dd').data("loaded", "true");
		  $(img).attr('src', NAV.imagePath + '/images/networkexplorer/collapse.gif');
	      });
    }
    if (expand_type == "swport"){
	$.get('/networkexplorer/expand/swport',
	      { 'swportid': expand_id },
	      function(data){
		  $(img).parent('dd').append(data);
		  $(img).parent('dd').data("loaded", "true");
		  $(img).attr('src', NAV.imagePath + '/images/networkexplorer/collapse.gif');
	      });
    }
};


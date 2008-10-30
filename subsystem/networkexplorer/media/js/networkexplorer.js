/**
	JavaScript functions for NetworkExplorer
**/

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

    $('#working').toggle(); 
    var moved = false;
	
    $.getJSON('/networkexplorer/search', parameters,
		function(data){

		var num_routers = data.routers.length;
		var num_gwports = data.gwports.length;
		var num_swports = data.swports.length;

		$.ajaxSetup({
				  async: false
		});

		$.each(data.routers,
			function(i, router){
				$('#router-'+ router[0]).css('font-weigth', 'bold');
				$($('#router-'+ router[0]).children().select('img')).parent('dd').append(router[1]);
				$($('#router-'+ router[0]).children().select('img')).parent('dd').data("loaded", "true");
				$($('#router-'+ router[0]).children().select('img')).parent('dd').children().select("dl").not("img").show();
				        $($('#router-'+ router[0]).children().select('img:first')).attr('src', '/images/networkexplorer/collapse.gif');
			if (!moved){
				document.location = '#router-' + router[0];
				moved = true;
			}
			});
		$.each(data.gwports,function(i,gwport){
		    var element = $('#gwport-' + gwport[0]);
			var element_parent = $(element.children().select('img')).parent('dd');
			element.addClass('highlight');
			element_parent.append(gwport[1]);
			element_parent.data("loaded","true");
			element_parent.children().select("dl").not("img").show();
             		$(element.children().select('.expand')).attr('src', '/images/networkexplorer/collapse.gif');
		});
        
        $.each(data.swports, function(i, swport){
            $('#swport-'+ swport[0]).addClass('highlight');
            $('#swport-'+ swport[0]).children().addClass('service_match');
            $($('#swport-'+ swport[0]).children().select('img')).parent('dd').append(swport[1]);
            $($('#swport-'+ swport[0]).children().select('img')).parent('dd').data("loaded", "true");
            $($('#swport-'+ swport[0]).children().select('img')).parent('dd').children().select("dl").not("img").show();
            $($('#swport-'+ swport[0]).children().select('img:first')).attr('src', '/images/networkexplorer/collapse.gif');
        });
    });

        $('#working').toggle(); 
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


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
				$.get('/networkexplorer/expand/router', { 'netboxid': router },
					function(data){
						$('#router-'+ router).css('font-weigth', 'bold');
						$($('#router-'+ router).children().select('img')).parent('li').append(data);
						$($('#router-'+ router).children().select('img')).parent('li').data("loaded", "true");
						$($('#router-'+ router).children().select('img')).parent('li').children().select("ul").not("img").show();
						
						// We dont want to start fetching gwports before
						// we are done with the routers. Messes up the dom-tree
						num_routers -= 1;
						if (num_routers < 1) gwports();
					});
			});
         
		function gwports(){
			var moved = false;
			$.each(data.gwports,function(i,gwport){
				$.get('/networkexplorer/expand/gwport', {'gwportid':gwport},
				function(data){
					var element = $('#gwport-' + gwport);
					var element_parent = $(element.children().select('img')).parent('li');
					element.addClass('gwport_match');
					element_parent.append(data);
					element_parent.data("loaded","true");
					element_parent.children().select("ul").not("img").show();
					if (!moved){
						document.location = '#gwport-' + gwport;
						moved = true;
					}
					num_gwports=-1;
					if(num_gwports<1) swports();
				});
			});
		};
            function swports(){
            $.each(data.swports, function(i, swport){
                    $.get('/networkexplorer/expand/swport',
                    { 'swportid': swport },
                    function(data){
                        $('#swport-'+ swport).addClass('swport_match');
                        $('#swport-'+ swport).children().addClass('service_match');
                        $($('#swport-'+ swport).children().select('img')).parent('li').append(data);
                        $($('#swport-'+ swport).children().select('img')).parent('li').data("loaded", "true");
                        $($('#swport-'+ swport).children().select('img')).parent('li').children().select("ul").not("img").show();
                    });
            });
            };
        });

        return false;
    });
});

function openNode(img){
    var expand_type = $(img).parent().attr('id').substr(0,6);
    var expand_id   = $(img).parent().attr('id').substr(7);

    // We dont want to double-load data and such,
    // so we set/check a state for that tree-node
    if ($(img).parent('li').data('working') == "true"){
        return false;
    } else {
        $(img).parent('li').data('working', 'true');
    }


    if ($(img).parent('li').data("loaded") == "true"){
        $(img).parent('li').children().select("ul").not("img").toggle();
        $(img).parent('li').data('working', 'false');
        return false;
    }

    // We want to show/hide nodes when we actually have any data to show/hide
    $(img).parent('li').ajaxSuccess(
        function(){
            $(img).parent('li').data('working', "false");
        });
 
    if (expand_type == "router"){
        $.get('/networkexplorer/expand/router',
            { 'netboxid': expand_id },
            function(data){
                $(img).parent('li').append(data);
                $(img).parent('li').data("loaded", "true");
            });
    }
    if (expand_type == "gwport"){
        $.get('/networkexplorer/expand/gwport',
            { 'gwportid': expand_id },
            function(data){
                $(img).parent('li').append(data);
                $(img).parent('li').data("loaded", "true");
            });
    }
    if (expand_type == "swport"){
        $.get('/networkexplorer/expand/swport',
            { 'swportid': expand_id },
            function(data){
                $(img).parent('li').append(data);
                $(img).parent('li').data("loaded", "true");
            });
    }
};


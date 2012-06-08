function postwith (to,p) {
    var myForm = document.createElement("form");
    myForm.method="post" ;
    myForm.action = to ;
    for (var k in p) {
        var myInput = document.createElement("input") ;
        myInput.setAttribute("name", k) ;
        myInput.setAttribute("value", p[k]);
        myForm.appendChild(myInput) ;
    }
    document.body.appendChild(myForm) ;
    myForm.submit() ;
    document.body.removeChild(myForm) ;
}


String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
        return typeof args[number] != 'undefined'
            ? args[number]
            : match
            ;
    });
};

function drawTrafficGradientSidebar(gradient) {
    var chart = $('#loadbar-chart')[0],
        w = 100,
        h = 196*2,
        r = 6,
        fill = d3.scale.category20(),
        trans=[0,0],
        scale=1;

    var svg = d3.select("#loadbar-chart")
        .append("svg:svg")
        .attr("width", w)
        .attr("height", h)

    svg.selectAll("rect").data(gradient)
        .enter()
        .append("svg:rect")
        .attr("width", "100")
        .attr("height", "2")
        .attr("style", function (d) {

            return 'fill:rgb('+parseInt(d[0])+','+parseInt(d[1])+','+parseInt(d[2])+');stroke-width:1;'
        })
        .attr('y', function (d,i) { return i*2 })
}



$(function () {

    $("#dropdown_view_id").change(function() {
        var state = $('select#dropdown_view_id :selected').val();
        if(state == "") state="-1";
        if (state != "-1") {
            load_view(state, true);
        }
        return false;
    });

    // handles save button in sidebar for updating/creatina new view
    $("#save_view").click(function() {
       var view_id = $('select#dropdown_view_id :selected').val();
        if (view_id == "-1") {
            //$('#modal_new_view').modal('toggle');
            $('#modal_new_view').dialog();
        } else {
            spinner_save_view.spin(document.getElementById("save_view_spinner"));

            $('<div style="background: #c0c0c0"></div>').appendTo($
                    ('#chart_header'))
                    .html('<div style="background:#c0c0c0;color: blue"><h6>Yes updating,no for new view</h6></div>')
                    .dialog({
                        modal: true, title: 'Delete message', zIndex: 10000, autoOpen: true,
                        width: 'auto', modal: true, resizable: false,
                        buttons: {
                            Yes: function () {
                                // $(obj).removeAttr('onclick');
                                // $(obj).parents('.Parent').remove();
                                save_view(view_id, {},
                                        function() { // success
                                            alert("view saved!");
                                            spinner_save_view.stop();
                                        },
                                        function() { // error
                                            show_error("Error while saving view");
                                            spinner_save_view.stop();
                                        }
                                );
                                $(this).dialog("close");
                            },
                            No: function () {
                                $(this).dialog("close");
                                $('#modal_new_view').dialog();
                            }
                        },
                        close: function (event, ui) {
                            $(this).remove();
                        }
                    });
        }
       return false;
    });

    $("#save_new_view").click(function() {
        spinner.spin(document.getElementById("modal_new_view"));

        data = {
            'title': $('input#new_view_title').val(),
            'description': $('textarea#new_view_description').val(),
            'is_public': (!!($('input#new_view_is_public').val() == "on"))
        }
        save_view(null, data,
                function(response, textstatus,jqXHR) { // success
                    console.log(response);
                    console.log("view saved! page refresh required due to " +
                            "alpha-test");
                    var view_id = jqXHR.getResponseHeader("x-nav-viewid")
                            || null

                    window.location = "/netmapdev/v/{0}".format(view_id);

                    spinner.stop();
                },
                function(response) { // error
                    console.log(response);
                    show_error_message(response.responseText);
                    spinner.stop();
                }
        );
        return false;
    })

    var TRAFFIC_META = {
        'tib': 1099511627776,
        'gib': 1073741824,
        'mib': 1048576,
        'kib': 1024,
        'tb': 1000000000000,
        'gb': 1000000000,
        'mb': 1000000,
        'kb': 1000
    }

    function save_view(view_id, data, on_success, on_error) {
        fixed_nodes = []


        for (i in json.nodes) {
            if (json.nodes[i].fixed === true) {
                fixed_nodes.push(json.nodes[i]);
            }
        }

        data['fixed_nodes'] = JSON.stringify(fixed_nodes);
        data['link_types'] = "2";
        data['zoom'] = [trans, scale].join(";");

        post_url = '/netmapdev/newview';
        if (view_id) {
            post_url = "/netmapdev/v/{0}/save".format(view_id);;
        }
        $.ajax({
            type: 'POST',
            url: post_url,
            data: data,
            success: on_success,
            error: on_error
        });
        /*postwith("/netmapdev/v/default/save", {
         'fixed_nodes' : JSON.stringify(fixed_nodes)
         });*/

    }

    // SI Units, http://en.wikipedia.org/wiki/SI_prefix
    function convert_bits_to_si(bits) {
        if (bits >= TRAFFIC_META['tb']) { return '{0}Tbps'.format(Math.round(((bits / TRAFFIC_META['tb'])*100)/100)) }
        else if (bits >= TRAFFIC_META['gb']) { return '{0}Gbps'.format(Math.round(((bits / TRAFFIC_META['gb'])*100)/100)) }
        else if (bits >= TRAFFIC_META['mb']) { return '{0}Mbps'.format(Math.round(((bits / TRAFFIC_META['mb'])*100)/100)) }
        else if (bits >= TRAFFIC_META['kb']) { return '{0}Kbps'.format(Math.round(((bits / TRAFFIC_META['kb'])*100)/100)) }
        return '{0}b/s'.format(Math.round((bits*100)/100))
    }

    var chart, svg, spinner, spinner_save_view, trans, scale;
    var spinner_opts = {
        lines: 11, // The number of lines to draw
        length: 11, // The length of each line
        width: 11, // The line thickness
        radius: 39, // The radius of the inner circle
        rotate: 58, // The rotation offset
        color: '#000', // #rgb or #rrggbb
        speed: 1.1, // Rounds per second
        trail: 39, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
    };
    var spinner_save_view_opts = {
            lines: 11, // The number of lines to draw
            length: 5, // The length of each line
            width: 2, // The line thickness
            radius: 4, // The radius of the inner circle
            rotate: 58, // The rotation offset
            color: '#000', // #rgb or #rrggbb
            speed: 1.1, // Rounds per second
            trail: 39, // Afterglow percentage
            shadow: false, // Whether to render a shadow
            hwaccel: false, // Whether to use hardware acceleration
            className: 'spinner', // The CSS class to assign to the spinner
            zIndex: 2e9, // The z-index (defaults to 2000000000)
            top: 'auto', // Top position relative to parent in px
            left: 'auto' // Left position relative to parent in px
    };
    var target = document.getElementById('loading_chart');
    spinner = new Spinner(spinner_opts)
    spinner_save_view = new Spinner(spinner_save_view_opts);

    function load_view(view_id) {
        spinner.spin(target)

        load_data(view_id);

        chart = $('#chart')[0],
                w = chart.offsetWidth,
                h = screen.height-500,
                r = 6,
                fill = d3.scale.category20(),
                trans=[0,0],
                scale=1;

        if (svg) { $('#svg-netmap').remove(); }

        svg = d3.select("#chart")
                        .append("svg:svg")
                        .attr('id', 'svg-netmap')
                        .attr("width", w)
                        .attr("height", h)
                        .attr("pointer-events", "all")
                        .append('svg:g')
                        .call(d3.behavior.zoom().on("zoom", redraw))
                        .append('svg:g')
                ;

        svg
                .append('svg:rect')
                .attr('width', w)
                .attr('height', h)
                .attr('fill', 'white');
        ;
    }

    function show_error_message(data) {

        var html="<div id='alert_message' class='alert alert-error " +
                "alert-block'>"
                +"<a class='close' data-dismiss='alert' href='#'>×</a>"
                +"<h4 class='alert-heading'>Error!</h4>"
                +"<p id='alert_message_content'>"+data+"</p>"
                +"</div>";
        $('#chart_header').append(html);
        spinner.stop();
    }

    function show_error(data_url) {
        var message = "Unable to load data from: <a href='"+data_url+"'>"
                +data_url+"</a><br />Please visit link,"
                +"copy stacktrace and file a bug on LaunchPad";
        var html="<div id='alert_message' class='alert alert-error " +
                "alert-block'>"
            +"<a class='close' data-dismiss='alert' href='#'>×</a>"
            +"<h4 class='alert-heading'>Error!</h4>"
            +"<p id='alert_message_content'>"+message+"</p>"
        +"</div>";

        $('#chart_header').append(html);

        spinner.stop();
    }


    function redraw() {
        trans=d3.event.translate;
        scale=d3.event.scale;
        //console.log("redraw(trans: "+trans+" , scale: "+scale+ ")");

        svg.attr("transform",
            "translate(" + trans + ")"
                + " scale(" + scale + ")");
    }

    json = {}
    var draw = function(data) {
        json = data

        /*index_a = Math.floor((Math.random()*json.nodes.length))
         a = json.nodes[index_a]
         b = json.nodes[Math.floor((Math.random()*json.nodes.length))]
         a.fixed = true;
         a.x = 50;
         a.y = 50;
         b.fixed = true;
         b.x = 800;
         b.y = 800;*/

        for (i in json.nodes) {
            if (json.nodes[i].data.position) {
                console.log(json.nodes[i]);
                json.nodes[i].x = json.nodes[i].data.position.x;
                json.nodes[i].y = json.nodes[i].data.position.y;
                json.nodes[i].fixed = true;
                console.log(json.nodes[i].data)
            }
        }


        var force = d3.layout.force().gravity(0.1).charge(-2500).linkDistance(250).size([w, h])
            .nodes(json.nodes).links(json.links).on("tick", tick).start();

        //0-100, 100-512,512-2048,2048-4096,>4096 Mbit/s
        var s_link = svg.selectAll("g line").data(json.links)

        s_link.enter().append("svg:g").attr("class", "link").forEach(function (d,i) {

            var gradient = s_link
                .append("svg:linearGradient")
                .attr("id", function(d,i) { return 'linkload'+i; })
                .attr('x1', '0%')
                .attr('y1', '0%')
                .attr('x2', '0%')
                .attr('y2', '100%');
            gradient
                .append("svg:stop")
                .attr('offset', '0%')
                .attr('style', function(d) {
                    if (d.data.traffic.inOctets_css) return 'stop-color:rgb('+d.data.traffic.inOctets_css+');stop-opacity:1'
                    else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                });
            gradient
                .append("svg:stop")
                .attr('offset', '50%')
                .attr('style', function(d) {
                    if (d.data.traffic.inOctets_css) return 'stop-color:rgb('+d.data.traffic.inOctets_css+');stop-opacity:1'
                    else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                });
            gradient
                .append("svg:stop")
                .attr('offset', '51%')
                .attr('style', function(d) {
                    if (d.data.traffic.outOctets_css) return 'stop-color:rgb('+d.data.traffic.outOctets_css+');stop-opacity:1'
                    else return 'stop-color:rgb(0,0,0);stop-opacity:1'

                });
            gradient
                .append("svg:stop")
                .attr('offset', '100%')
                .attr('style', function(d) {
                    if (d.data.traffic.outOctets_css) return 'stop-color:rgb('+d.data.traffic.outOctets_css+');stop-opacity:1'
                    else return 'stop-color:rgb(0,0,0);stop-opacity:1'
                });
            s_link.append("svg:line")
                .attr("class", function(d,i) {
                    var speed = d.data.link_speed;
                    var classes = "";
                    if(speed<=100){ classes = 'speed0-100' }
                    else if(speed>100 && speed<=512){ classes = 'speed100-512' }
                    else if(speed>512 && speed<=2048){ classes = 'speed512-2048' }
                    else if(speed>2048 && speed<=4096){ classes = 'speed2048-4096'}
                    else if(speed>4096){ classes = 'speed4096'}
                    else { classes = 'speedunknown'}
                    if (d.data.tip_inspect_link) { classes=classes+" warning_inspect"}
                    return classes;

                })
                .attr('stroke', function(d,i) { return 'url(#linkload'+i+')'})
                .on("mouseover", function(d) { return link_popup(d) })
                .on("mouseout", function(d) { return link_popout(d) });
        });

        var link = svg.selectAll("g.link line")

        var node_s = svg.selectAll("g circle").data(json.nodes);
        //var drag = d3.behavior.drag()
        //      .origin(Object)
        //.call(d3.behavior.zoom().on("zoom", redraw))
        var node_drag =
            d3.behavior.drag()
                .on("dragstart", dragstart)
                .on("drag", dragmove)
                .on("dragend", dragend);


        node_s.enter().append("svg:g")
            .attr("class", "node")
            .append("svg:image")
            .attr("class", "circle node")
            .attr("xlink:href", function (d) {
                return "http://stud-1201:8888/images/netmap/"+ d.data.category.toLowerCase() + ".png";
            })
            .attr("x", "-16px")
            .attr("y", "-16px")
            .attr("width", "32px")
            .attr("height", "32px");

        node_s.enter().forEach(function (d) {
            node_s.append("svg:text")
                .attr("dy", "1.5em")
                .attr("class", "node")
                .attr("text-anchor", "middle")
                .attr("fill", "#000000")
                .attr("background", "#c0c0c0")
                .text(function (d) {
                    return d.name
                })
        });
        var node = svg.selectAll("g.node");

        node
            .call(node_drag)
            .on("mouseover", function(d) { return node_mouseOver(d) })
            .on("mouseout", function(d) { return node_mouseOut(d) })
            .on("click", node_onClick)
        ;
        /*node.selectAll("circle").append("title").text(function (d) {
         return d.name;
         });*/

        spinner.stop();


        function tick() {


            //console.log(node);
            node.attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

            link
                .attr("x1",function (d) { return d.source.x;})
                .attr("y1",function (d) { return d.source.y;})
                .attr("x2",function (d) { return d.target.x;})
                .attr("y2", function (d) { return d.target.y;}
            );

            //node.call( function (d,i) { return node_drag(d,i) });



        }

        var linkedByIndex = {};
        json.links.forEach(function (d) {
            linkedByIndex[d.source.index + "," + d.target.index] = 1;
        });

        function isConnected(a, b) {
            return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index] || a.index == b.index;
        }

        function dragstart(d, i) {
            force.stop()
        }

        function dragmove(d, i) {
            d.px += d3.event.dx;
            d.py += d3.event.dy;
            d.x += d3.event.dx;
            d.y += d3.event.dy;
            tick();
        }

        function dragend(d, i) {
            console.log("dragend: " + d.data.sysname);
            d.fixed = true;
            tick();
            force.resume();
        }

        function node_mouseOver(d) {
            mover({'title':d.name, 'description':'', 'css_description_width': 200});
            fade(d, 0.1);
        }

        function node_mouseOut(d) {
            mout(d);
            fade(d, 1);
        }

        function fade(d, opacity) {
            node.style("stroke-opacity", function (o) {
                thisOpacity = isConnected(d, o) ? 1 : opacity;
                this.setAttribute('fill-opacity', thisOpacity);
                this.setAttribute('opacity', thisOpacity);

                circle = (this.firstElementChild || this.children[0] || {})

                text = (this.childNodes[1] || {})

                v = circle.textContent
                if (d.name == v) {
                    circle.setAttribute("style", "fill: red");
                    text.setAttribute("style", "fill: red");
                } else {
                    circle.setAttribute('style', "fill: " + fill(d.group));
                    text.setAttribute('style', "fill: #000");
                }


                return thisOpacity;
            });


            link.style("stroke-opacity", function (o) {
                return o.source === d || o.target === d ? 1 : opacity;
            });

        }

        function link_popup(d) {
            //console.log(d)
            mover({
                'title':'link',
                'description': d.data.uplink.thiss + " -> " + d.data.uplink.other +
                    '<br />'+ d.data.link_speed +
                    '<br />In: '+ convert_bits_to_si(d.data.traffic['inOctets'].raw*8) + " raw["+ d.data.traffic['inOctets'].raw+"]"+
                    '<br />In: '+ convert_bits_to_si(d.data.traffic['outOctets'].raw*8) + " raw["+ d.data.traffic['outOctets'].raw+"]"
                ,
                'css_description_width': 400
            });

        }

        function link_popout(d) {
            mout(d);
        }

        function mover(d) {
            //console.log('mover!');
            $("#pop-up").fadeOut(100,function () {
                // Popup content
                $("#pop-up-title").html(d.title);
                $("#pop-img").html("23");
                $("#pop-desc").html(d.description).css({'width':d.css_description_width});

                // Popup position

                //console.log(scale);
                //console.log(trans);

                var popLeft = (d.x*scale)+trans[0]-10;//lE.cL[0] + 20;
                var popTop = (d.y*scale)+trans[1]+70;//lE.cL[1] + 70;
                $("#pop-up").css({"left":popLeft,"top":popTop});
                $("#pop-up").fadeIn(100);
            });

        }

        function mout(d) {
            $("#pop-up").fadeOut(50);
            //d3.select(this).attr("fill","url(#ten1)");
        }

        function link_onClick(link) {
            //return link_popup();
            //console.log(link.data.uplink.this + " -> " + link.data.uplink.other);
        }

        function node_onClick(node) {
            $("#nodeinfo").html(
                "<span><img src='/images/lys/"+node.data.up_image+"' alt='"+node.data.up+"' class='netmap-node-status' />" +
                    "<h2>"+node.data.sysname+"</h2></span>" +
                    "<p>Last updated: "+node.data.last_updated + "</p>" +
                    "<ul class='netmap-node-menu'>" +
                    "<li>[<a href='"+node.data.ipdevinfo_link+"'>infodevinfo</a>]</li>" +
                    "<li>[<a href='#'>geomap</a>]</li>" +
                    "</ul>" +
                    "<dl>" +
                    "<dt>IP</dt>" +
                    "<dd>"+node.data.ip+"</dd>" +
                    "<dt>Category</dt>" +
                    "<dd style='background: url(\/images\/netmap\/"+node.data.category.toLowerCase()+".png) no-repeat; background-size: 32px 32px; padding-left: 35px; min-height: 32px; height: 32px'>"+node.data.category+"</dd>" +
                    "<dt>Type</dt>" +
                    "<dd>"+node.data.type+"</dd>" +
                    "<dt>Room</dt>" +
                    "<dd>"+node.data.room+"</dd>" +
                    "</dl>"


            );
        }

        /*svg.style("opacity", 1e-6)
         .transition()
         .duration(1000)
         .style("opacity", 1);*/

    }


    view_id = $("#netmapview_id").text().trim();
    load_view(view_id);

    function load_data(view_id) {
        dataUrl = 'http://stud-1201:8888/netmapdev/data/d3js/layer2'
        if (view_id) {
            dataUrl = dataUrl+"/"+view_id
        }
        console.log(dataUrl);
        $.ajax({
            url: dataUrl
            ,success: function(data) {
                draw(data);
            },
            error: function (foo) { show_error(dataUrl) },
            cache: false,
            dataType: 'json',
            mimeType: 'application/json',
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Expires': -1
            }
        });
    }


    $.ajax({
        url: 'http://stud-1201:8888/netmapdev/data/traffic_load_gradient'
        ,success: function(data) {
            drawTrafficGradientSidebar(data);
        },
        cache: false,
        dataType: 'json',
        mimeType: 'application/json',
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': -1
        }
    });

    //d3.json('http://stud-1201:8888/netmapdev/data/d3js/layer2?c='+new Date().getTime(), function(load) {
    //    draw(load);
    //});
});





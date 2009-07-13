# config.py: Configuration file for Geomap.
#
# Warning: Despite the name, this file is NOT a Python file.  The
# '.py' in the name is there because the syntax is sufficiently
# similar to Python to make it beneficial to edit the file in Python
# mode.

def variant(normal, "Normal"):

    template_file(node_popup, "popup_place.html")
    template_file(edge_popup, "popup_network.html")

    def indicator(edge, color, "Link load"):
        if load != load:
            ("#666666", "No statistics")
        if load/speed < 0.01:
            ("#0099FF", "0--1 %")
        if load/speed < 0.05:
            ("#66CCFF", "1--5 %")
        if load/speed < 0.10:
            ("#99FF00", "5--10 %")
        if load/speed < 0.30:
            ("#CCFF00", "10--30 %")
        if load/speed < 0.50:
            ("#FFFF00", "30--50 %")
        if load/speed < 0.70:
            ("#FFCC00", "50--70 %")
        if load/speed < 0.90:
            ("#FF9900", "70--90 %")
        if True:
            ("#FF3333", "90--100 %")

    def indicator(edge, size, "Link capacity"):
        if speed <= 2:
            (4, "<= 2 Mbit/s")
        if speed <= 155:
            (6, "<= 155 Mbit/s")
        if speed <= 2500:
            (8, "<= 2.5 Gbit/s")
        if True:
            (10, "> 2.5 Gbit/s")

    def indicator(node, color, "CPU load"):
        if load != load:
            ("#666666", "No statistics")
        if load < 0.5:
            ("#33CC33", "0--0.5")
        if load < 1:
            ("#FFEF00", "0.5--1")
        if True:
            ("#FF3333", "> 1")

    def indicator(node, size, "# netboxes"):
        if num_netboxes == 1:
            (4, "1")
        if num_netboxes <= 10:
            (6, "2--10")
        if num_netboxes <= 20:
            (8, "11--20")
        if True:
            (10, "> 20")

    
def variant(open, "Open"):

    template_file(node_popup, "popup_place_open.html")
    template_file(edge_popup, "popup_network_open.html")

    style(edge, color, "black")
    style(edge, size, 8)
    style(node, color, "black")
    style(node, size, 10)

    def indicator(edge, size, "Link capacity"):
        if speed <= 2:
            (4, "<= 2 Mbit/s")
        if speed <= 155:
            (6, "<= 155 Mbit/s")
        if speed <= 2500:
            (8, "<= 2.5 Gbit/s")
        if True:
            (10, "> 2.5 Gbit/s")

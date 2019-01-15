# config.py: Configuration file for Geomap.
#
# Warning: Despite the name, this file is NOT a Python file.  The
# '.py' in the name is there because the syntax is sufficiently
# similar to Python to make it beneficial to edit the file in Python
# mode.


def variant(normal, "Map with sensitive information"):

    template_file(node_popup, "popup_place.html")
    template_file(edge_popup, "popup_network.html")

    def indicator(edge, color, "Link load"):
        if is_nan(load_out) or capacity == 0:
            ("#666666", "No statistics")
        if load_out/capacity < 0.3:
            ("#8AE234", "0--30 %")
        if load_out/capacity < 0.6:
            ("#FCE94F", "30--60 %")
        if load_out/capacity < 0.9:
            ("#FCAF3E", "60--90 %")
        if True:
            ("#CC0000", "90--100 %")

    def indicator(edge, size, "Link capacity"):
        if capacity <= 2:
            (4, "<= 2 Mbit/s")
        if capacity <= 155:
            (6, "<= 155 Mbit/s")
        if capacity <= 2500:
            (8, "<= 2.5 Gbit/s")
        if True:
            (10, "> 2.5 Gbit/s")

    def indicator(node, color, "CPU load"):
        if is_nan(load):
            ("#666666", "No statistics")
        if load < 50:
            ("#8AE234", "0--0.5")
        if load < 100:
            ("#FCE94F", "0.5--1")
        if load >= 100:
            ("#CC0000", "> 1")

    def indicator(node, size, "# netboxes"):
        if num_netboxes == 1:
            (4, "1")
        if num_netboxes <= 10:
            (6, "2--10")
        if num_netboxes <= 20:
            (8, "11--20")
        if True:
            (10, "> 20")


def variant(open, "Map with open information"):

    template_file(node_popup, "popup_place_open.html")
    template_file(edge_popup, "popup_network_open.html")

    def indicator(edge, color, "Link load"):
        if is_nan(load_out) or capacity == 0:
            ("#666666", "No statistics")
        if load_out/capacity < 0.3:
            ("#8AE234", "0--30 %")
        if load_out/capacity < 0.6:
            ("#FCE94F", "30--60 %")
        if load_out/capacity < 0.9:
            ("#FCAF3E", "60--90 %")
        if True:
            ("#CC0000", "90--100 %")

    def indicator(edge, size, "Link capacity"):
        if capacity <= 2:
            (4, "<= 2 Mbit/s")
        if capacity <= 155:
            (6, "<= 155 Mbit/s")
        if capacity <= 2500:
            (8, "<= 2.5 Gbit/s")
        if True:
            (10, "> 2.5 Gbit/s")

    def indicator(node, color, "CPU load"):
        if is_nan(load):
            ("#666666", "No statistics")
        if load < 50:
            ("#8AE234", "0--0.5")
        if load < 100:
            ("#FCE94F", "0.5--1")
        if load >= 100:
            ("#CC0000", "> 1")

    def indicator(node, size, "# netboxes"):
        if num_netboxes == 1:
            (4, "1")
        if num_netboxes <= 10:
            (6, "2--10")
        if num_netboxes <= 20:
            (8, "11--20")
        if True:
            (10, "> 20")

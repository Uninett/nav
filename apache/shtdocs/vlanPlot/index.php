<HTML>
 <HEAD>
  <title>vlanPlot</title>
 </HEAD>
 <BODY bgcolor="#FFFFFF">
  <APPLET
   ARCHIVE="common/vlanPlot.jar"
   CODE="vlanPlot.class"
   CODEBASE="."
   WIDTH=800 HEIGHT=600
   >
   <?php
     include("/usr/local/nav/local/etc/conf/vlanPlotS.conf");
     if ($boksid != "") echo "<PARAM NAME=\"gotoBoksid\" VALUE=\"$boksid\">";
     if ($vlan != "") echo "<PARAM NAME=\"gotoVlan\" VALUE=\"$vlan\">";
   ?>
  </APPLET>
  <BR>
  <A HREF="common/omvlanplot.html" target="_blank">Om vlanPlot v2.0</A>
 </BODY>
</HTML>

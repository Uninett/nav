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
   <PARAM NAME="vPServerURL" VALUE="https://www.nav.ntnu.no/vPServerNG/servlet/vPServer">
   <PARAM NAME="lastURL" VALUE="https://www.nav.ntnu.no/vlanPlotNG/common/vPLast/last_ny.pl">
   <PARAM NAME="cricketURL" VALUE="http://www.nav.ntnu.no/~cricket/">
   <PARAM NAME="netflowURL" VALUE="http://manwe.itea.ntnu.no/">
   <?php
     if ($boksid != "") echo "<PARAM NAME=\"gotoBoksid\" VALUE=\"$boksid\">";
     if ($vlan != "") echo "<PARAM NAME=\"gotoVlan\" VALUE=\"$vlan\">";
   ?>
  </APPLET>
  <BR>
  <A HREF="common/omvlanplot.html" target="_blank">Om vlanPlot v2.0</A>
 </BODY>
</HTML>

<?php

function navstart($title,$remote_user) {
  global $REMOTE_ADDR,$SERVER_NAME,$REMOTE_USER;
  $menybredde = "100%";


$navme = '/usr/local/nav/navme/apache/vhtdocs';
$local = '/usr/local/nav/local/apache/vhtdocs';

$htpasswd = '/usr/local/nav/navme/apache/htpasswd';
$passwdfil   = "$htpasswd/.htpasswd-sroot";

# NAVME-filer
$header = "$navme/header.html";
$nav = "$navme/nav.html";
$bruker = "$navme/bruker.html";

# Lokale filer
$linker = "$local/linker.html";
$kontakt = "$local/kontakt.html";


if ($remote_user == '') {
  $omraade = 'aapen';
}
else {
  $innhold = file($passwdfil);
  foreach ($innhold as $element) {
    if (!preg_match("/^\W/",$element)) {
      list($user, $passord, $navn, $merknader, $omraade) = split(":", $element);
      $user_data[$user]['omraade'] = chop($omraade);
      }
    $omraade = $user_data[$remote_user]['omraade'];
  }	    
}


  $remote_ip = $REMOTE_ADDR;
  $servername = $SERVER_NAME;
  
  print "<html><head><title>$title</title>\n";
  print "<body bgcolor=#ffffff text=#000000>\n";
  print "<table><tr><td bgcolor=#ffffff colspan=2>\n";
  
  $topp = file($header);
  foreach ($topp as $element) { 
    print $element; 
  }
  
  print "</td></tr>\n";
  print "<tr><td valign=top>\n";
  print "<table width=$menybredde bgcolor=#000000 border=0 cellpadding=0 cellspacing=1>\n";
  print "<tr><td>\n";
  print "<table width=$menybredde cellspacing=1 border=0 cellpadding=2 bgcolor=#e6e6e6>\n";
  print "<tr><td bgcolor=#486591><font color=#ffffff>\n";
  print "<strong><font color=#fefefe>NAV</font></strong></font></td></tr></table>";
  print "<table width=$menybredde cellspacing=1 border=0 cellpadding=7 bgcolor=#fefefe>\n";
  print "<tr><td bgcolor=#e6e6e6>";

  $content = file($nav);
  foreach ($content as $element) { 
    print $element; 
  }
  
  print "</td></tr></table></td></tr></table><p>";
  
####################################################
  print "<table width=$menybredde bgcolor=#000000 border=0 cellpadding=0 cellspacing=1>";
  print "<tr><td><table width=$menybredde cellspacing=1 border=0 cellpadding=2 bgcolor=#e6e6e6>";
  print "<tr><td bgcolor=#486591><font color=#ffffff><strong><font color=#fefefe>Bruker";

  if (strtolower($omraade) == 'aapen') {
    print "<a href=https://$servername/>Logg inn</a>&nbsp;<a href=/doc/hjelp.html>Hjelp</a>";
  }

  if (strtolower($omraade) == 'begrenset') {
    print "<a href=/sec/>Logg inn</a>";  
  }
  print "</font></strong></font>
	  </td>
	  </tr>
	  </table>
	  <table width=$menybredde cellspacing=1 border=0 cellpadding=7 bgcolor=#fefefe>
	  <tr><td bgcolor=#e6e6e6>
	  <table>
	  <tr><td><b>BRUKER:</td><td>$remote_user</td></tr>
	  <tr><td><b>ADGANG:</td><td>".$omraade."</td></tr>
	  </table>";

print "<p>";

 if ($omraade != 'aapen') {
   $innhold = file ($bruker);
   foreach ($innhold as $element) { 
     print $element; 
   }
 }
   print "
	  </td>
	  </tr>
	  </table>
	  </td>
	  </tr>
	  </table>
	  <p>
	  ";
 
 print "
	  <table width=$menybredde bgcolor=#000000 border=0 cellpadding=0 cellspacing=1>
	  <tr><td>
	  <table width=$menybredde cellspacing=1 border=0 cellpadding=2 bgcolor=#e6e6e6>
	  <tr><td bgcolor=#486591><font color=#ffffff>
	  <strong><font color=#fefefe>Linker</font></strong>      </font>
	  </td></tr>
	  </table>
	  <table width=$menybredde cellspacing=1 border=0 cellpadding=7 bgcolor=#fefefe>
	  <tr><td bgcolor=#e6e6e6>
	  ";
 
 $innhold = file($linker);
 foreach ($innhold as $element) { 
   print $element; 
 }
 
 print "</td></tr></table></td></tr></table><p>";
 
 print "
<table width=$menybredde bgcolor=#000000 border=0 cellpadding=0 cellspacing=1>
 <tr><td>
   <table width=$menybredde cellspacing=1 border=0 cellpadding=2 bgcolor=#e6e6e6>
    <tr><td bgcolor=#486591><font color=#ffffff>
       <strong><font color=#fefefe>Kontakt</font></strong>      </font>
     </td></tr></table>
   <table width=$menybredde cellspacing=1 border=0 cellpadding=7 bgcolor=#fefefe>
   <tr><td bgcolor=#e6e6e6>
";

 $innhold = file($kontakt); 
 foreach ($innhold as $element) { 
   print $element; 
 }
 
 print "</td></tr></table></td></tr></table>";
 print "</td><td valign=top bgcolor=#ffffff>";
 print "<table border=0 cellpadding=10 cellspacing=1> <tr><td>";

}

function navslutt() {
  $footer = '/usr/local/nav/local/apache/vhtdocs/footer.html';
 
  print "</td></tr></table>";
  print "</td></tr>";
  print "<tr><td colspan=2>";

  $footer = file($footer);
  foreach ($footer as $element)
    { print $element; }
  print "</td></tr></table>";
}

?>
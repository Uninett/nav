<?php

function html_topp($tittel) {
  print "<html><head><title>$tittel</title></head><body bgcolor=white>";
}

function html_topp_tid($tittel,$tid,$url) {
  print "<html><head>";
  print "<META http-equiv=\"REFRESH\" content=\"$tid; url=$url\">";
  print "<title>$tittel</title></head><body bgcolor=white>";
}

function html_topp_script($tittel) {
  print "<html><head><title>$tittel</title>";
  print "<SCRIPT language=\"JavaScript\">\n";
  print "<!--\n";
}

function html_topp2_script() {
  print "//-->\n";
  print "</SCRIPT></head
>\n";
  print "<body bgcolor=white>";
}

# Tar inn to brukere og sjekker om navnene er like.
# Hvis ikke sjekker vi om det navnet som ikke er tatt
# av variabelen $REMOTE_USER har admin-rettigheter.
function verify_user($bruker,$remote) {
  $filename = "/usr/local/trapdetect/www/msyst.conf";
  $contents = file($filename);
  $admin = 0;
  
  foreach ($contents as $name) {
    $name = chop($name);
    if ($name == $remote) {
      $admin = 1;
    }
  }
  
  if (!$admin) {
    $bruker = $remote;
  }

  return array($bruker,$admin);
}

# Hjelpsom liten funksjon som skriver ut HTTP_POST_VARS
function skrivpost($array) {
  foreach (array_keys($array) as $key) {
    if ($key == "org") {
      $temp = $array[$key];
      foreach ($temp as $t) {
	print "$key -> $t<br>\n";
      }
    } else {
      print "$key -> $array[$key]<br>\n";
    }
  }
}

# Skriver ut en knapp som fører deg til hovedsiden
function knapp_hovedside($bruker) {
  print "<form action=meldingssystem_start.php method=POST>";
  print "<input type=hidden name=bruker value=$bruker>";
  print "<input type=submit value=\"Til hovedsiden\">\n";
  print "</form>\n";
}
?>
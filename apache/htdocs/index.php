<?php

/* $Id: index.php,v 1.2 2002/08/05 11:38:13 mortenv Exp $  */

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');

$htpasswd = '/usr/local/nav/local/apache/htpasswd';
$passwdfil = "$htpasswd/.htpasswd-sroot";

$navme = '/usr/local/nav/navme/apache/vhtdocs';
$local = '/usr/local/nav/local/apache/vhtdocs';

# NAVME-filer
$public = "$navme/public.html";
$restricted = "$navme/restricted.html";
$secret = "$navme/secret.html";

# Lokale filer
$l_intro      = "$local/intro.html";
$l_public     = "$local/public.html";
$l_restricted = "$local/restricted.html";
$l_secret     = "$local/secret.html";


# $remote_user = $REMOTE_USER;
$remote_user = $PHP_AUTH_USER;

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


###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
navstart("NAV",$remote_user);
###########################################


#print "USER: $remote_user<br>OMR: $omraade";
$innhold = file($l_intro);
foreach ($innhold as $element) { 
  print $element;
}


$innhold = file($public);
foreach ($innhold as $element) { 
  print $element;
}

$innhold = file($l_public);
foreach ($innhold as $element) { 
  print $element;
}


$temp = strtolower($user_data[$remote_user]['omraade']);
if ($temp == 'begrenset') {

#if ($omraade == 'begrenset') {
  $innhold = file($restricted);
  foreach ($innhold as $element) { 
    print $element;
  }
	
  $innhold = file($l_restricted);
  foreach ($innhold as $element) { 
    print $element;
  }
}

$temp = strtolower($user_data[$remote_user]['omraade']);
if ($temp == 'intern') {

#if ($omraade == 'intern') {

  $innhold = file($restricted);
  foreach ($innhold as $element) {
    print $element; 
  }
  $innhold = file($l_restricted);
  foreach ($innhold as $element) {
    print $element; 
  }


  $innhold = file($secret);
  foreach ($innhold as $element) {
    print $element; 
  }

  $innhold = file($l_secret);
  foreach ($innhold as $element) {
    print $element; 
  }


}

###########################################
# Kjører filen navslutt, og skriver "print-linjene" til web
navslutt();
###########################################


<?php 

require('meldingssystem.inc');
html_topp("Endringen er lagret");

$vars = $HTTP_POST_VARS;
if ($vars[sms] == 'on') {
  $vars[sms] = 'Y';
} else {
  $vars[sms] = 'N';
}
#skrivpost($vars);

list ($bruker,$admin) = verify_user($bruker,$REMOTE_USER);

# Oppretter kontakt med databasen.
$dbh = mysql_connect("localhost","nett","stotte");
mysql_select_db('trapdetect');

########################################
# Legger data inn i databasen
# Gjøres ved å oppdatere det som er der 
# fra før.
########################################
if ($admin && $ny) {
  $sporring = "insert into user (user,mail,tlf,status,sms,dsms_fra,dsms_til) values ";
  $sporring .= "('$bruker','$vars[mail]','$vars[tlf]','$vars[status]','$vars[sms]','$vars[dsmsfra]','$vars[dsmstil]')";
  $done = mysql_query($sporring);

  $hent_id = mysql_query("select id from user where user='$bruker'");
  $res = mysql_fetch_array($hent_id);
  
  foreach ($vars[org] as $element) {
    mysql_query("insert into useriorg (userid,orgid) values ($res[id],$element)");
  }
} else {
  $hent_id = mysql_query("select id from user where user='$bruker'");
  $res = mysql_fetch_array($hent_id);
  if ($admin) {
    $sporring = "update user set mail='$vars[mail]',tlf='$vars[tlf]',status='$vars[status]'";
    $sporring .= ",sms='$vars[sms]', dsms_fra='$vars[dsmsfra]',dsms_til='$vars[dsmstil]' where user='$bruker'";

    if ($vars[org]) {
# Sletter alle innlegg med denne brukerid
      $slett = mysql_query("delete from useriorg where userid=$res[id]");
# Legger inn alle valgte orgid
      foreach ($vars[org] as $element) {
	mysql_query("insert into useriorg (userid,orgid) values ($res[id],$element)");
      }
    }
  } else {
    $sporring = "update user set mail='$vars[mail]',tlf='$vars[tlf]',status='$vars[status]'";
    $sporring .= ",dsms_fra='$vars[dsmsfra]',dsms_til='$vars[dsmstil]' where user='$bruker'";
  }
  $done = mysql_query($sporring);
}
#print "$sporring<br>\n";

# Skriver status-melding
if ($done) {
  print "Databasen oppdatert. Gå tilbake til hovedsiden<br>\n";
} else {
  print "En feil skjedde under innlegging i databasen. Gå tilbake til hovedsiden<br>\n";
}

# Skriver tilbake-til-hovedsidenknapp
knapp_hovedside($bruker);

?>

</body></html>
<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("User administration"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>" . gettext("Here you can change and create new users, and set their permissions.");

echo '<p><a href="#nybruker">';
echo gettext("Add new user") . "</a>";
echo "<p>";

if (get_get('subaction') == 'endre') {
    session_set('endrebrukerid', get_get('cuid'));
}


if (get_get('subaction') == 'endret' ) {

	if (session_get('endrebrukerid') > 0) { 
		$dbh->endreBruker(session_get('endrebrukerid'), post_get('brukernavn'), post_get('navn'), 
			post_get('passord'), post_get('admin'), post_get('sms'), post_get('kolengde') );

		print "<p><font size=\"+3\">" . gettext("OK</font>, the user is changed.");

    	if (post_exist('epost')) {
    		$dbh->nyAdresse(post_get('epost'), 1, session_get('endrebrukerid') );
    		print gettext(" And a new e-mail address is added to the user.");
   		}
    

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the user is <b>not</b> changed.");
	}
	
}

if (get_get('subaction') == "slett") {
	
	if (get_get('cuid') > 0) { 
	
		$dbh->slettBruker(get_get('cuid') );

		print "<p><font size=\"+3\">" . gettext("OK</font>, the user is removed from the database.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error occured</font>, the user is <b>not</b> removed.");
	}


}

if (get_get('subaction') == "nybruker") {
  print "<h3>" . gettext("Registering a new user...") . "</h3>";
  
  
 
  
  $uid = $dbh->nyBruker(post_get('navn'), post_get('brukernavn'), post_get('passord'), 
  	post_get('admin'), post_get('sms'), post_get('kolengde'), &$error);

  if ($uid > 0) { 
    $navn = ""; $brukernavn = ""; $passord = ""; $admin = 1; $sms = 0;
    
    
 
    
    $profilid = $dbh->nyProfil('Standard', $uid, 0, 8, 0, 7,30 );
    $tidsid = $dbh->nyTidsperiode(1, '08:00', $profilid);
    
    $dbh->aktivProfil($uid, $profilid);
    if (isset($epost)) {
    	$dbh->nyAdresse(post_get('epost'), 1, $uid);
    }
    
    print "<p><font size=\"+3\">" . gettext("OK</font>, a new user with username $brukernavn is added to the database with user ID $uid. A new standard profile profile is created for the user (profile ID = $profilid). The profile has on time period, from 08:00 to 08:00 all days.");
	print '<p>You may want to <a href="index.php?action=brukertilgruppe&subaction=velge&vbuid=' . $uid . '">subscribe the suer to some user gruops</a>.';

  } else {
    print "<p><font size=\"+3\">" . gettext("An error occured</font>, a new user is <b>not</b> added to the database.");
  }


}

$l = new Lister( 102,
	array(gettext('User name'), gettext('Name'), gettext('Admin'), gettext('SMS'), 
		gettext('Queue'),gettext('#prof'), gettext('#adr'), gettext('Options..') ),
	array(15, 25, 10, 10, 5, 10, 10, 15),
	array('left', 'left', 'right', 'center', 'center', 'right', 'right', 'right'),
	array(true, true, true, true, true, true, true, false),
	1
);


print "<h3>" . gettext("Local users") . "</h3>";


if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


$brukere = $dbh->listbrukere($l->getSort() );

for ($i = 0; $i < sizeof($brukere); $i++) {

	if (get_get('subaction') == 'endre' AND session_get('endrebrukerid') == $brukere[$i][0]  ) {
		$brukernavn = $brukere[$i][1];
		$navn = $brukere[$i][2];
		$admin = $brukere[$i][3];		
		$csms = $brukere[$i][4];
		$kolengde = $brukere[$i][7];
	}

  if ($brukere[$i][4] == 't') { 
    $sms = '<img alt="Yes" src="icons/ok.gif">';
  } else {
    $sms = '<img alt="No" src="icons/cancel.gif">';
  }
  
  $valg = '<a href="index.php?action=brukertilgruppe&subaction=velge&vbuid=' . $brukere[$i][0] . '">' .
  	'<img alt="Velge grupper" src="icons/gruppe.gif" border=0></a>&nbsp;' .  	
  	'<a href="index.php?action=admin&subaction=endre&cuid=' . $brukere[$i][0] . '#nybruker">' . 
  	'<img alt="Edit" src="icons/edit.gif" border=0></a>&nbsp;' .
    '<a href="index.php?action=admin&subaction=slett&cuid=' . $brukere[$i][0]. '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

  if ($brukere[$i][5] > 0 ) 
    { $pa = $brukere[$i][5]; }
  else 
    {
      $pa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">";

    }

  if ($brukere[$i][6] > 0 ) 
    { $aa = $brukere[$i][6]; }
  else 
    { $aa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }

  switch ($brukere[$i][3]) {
  	case 0: $adm = "<img alt=\"Deaktivert\" src=\"icons/person0.gif\">";
  	break;
  	case 1: $adm = "<img alt=\"Standard\" src=\"icons/person1.gif\">";
  	break;
  	case 100: $adm = "<img alt=\"Admin\" src=\"icons/person100.gif\">";
  	break;
  	default: $adm = "<p>" . gettext("Unknown");  	
  }

  $l->addElement( array($brukere[$i][1],  // brukernavn
			$brukere[$i][2],  // navn
			$adm, // admin
			$sms,  // sms
			$brukere[$i][7], // kølengde
			$pa, 
			$aa,
			$valg
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php?action=" . $action. "\">" . gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Number of users: ") . sizeof($brukere);
?>
<a name="nybruker"></a><p><h3>
<?php
if (get_get('subaction') == 'endre') {
	echo gettext("Change user info");
} else {
	echo gettext("Add a new user");
}
?></h3>
<form name="form1" method="post" action="index.php?action=admin&subaction=<?php
if (get_get('subaction') == 'endre') echo "endret"; else echo "nybruker";
?>">



  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    <tr>
      <td width="30%"><p><?php echo gettext("Name"); ?></p></td>
      <td width="70%"><input name="navn" type="text" size="40" 
value="<?php echo $navn; ?>"></td>
    </tr>
    <tr>
      <td><?php echo gettext("E-mail"); ?></td>
      <td><input size="50" name="epost" type="text" 
value="<?php 
if ($subaction == 'endre') {
	echo $epost;
} else {
	echo gettext("bruker@uninett.no");
} ?>"><?php
if (get_get('subaction') == 'endre') {
	echo '&nbsp;<b>' . gettext("Add e-mail address??") . '</b>';
}
?>
</td>
    </tr>    
    <tr>
      <td><?php echo gettext("User name"); ?></td>
      <td><input name="brukernavn" type="text" 
value="<?php echo $brukernavn; ?>"></td>
    </tr>

    <tr>
      <td><?php echo gettext("Password"); ?></td>
      <td><input type="password" name="passord">
</td>
    </tr>
    <tr>
<?php
		
$ta[0] = ""; $ta[1] = ""; $ta[2] = ""; 
switch($admin) {
	case 0: $ta[0] = " selected"; break;
	case 100: $ta[2] = " selected"; break;
	default: $ta[1] = " selected";	
}
		
?>    
    
      <td><?php echo gettext("Administrator level"); ?></td>
      <td align="center"><select name="admin" id="select">
          <option value="0"<?php echo $ta[0] . ">" . gettext("0 Account deactivated"); ?> </option>
          <option value="1"<?php echo $ta[1] . ">" . gettext("1 Regular user"); ?> </option>
          <option value="100"<?php echo $ta[2] . ">" . gettext("100 Administrator"); ?> </option>
        </select></td>
    </tr>
    <tr>
    
<?php
		
$ta[0] = ""; $ta[1] = ""; $ta[2] = ""; $ta[3] = ""; $ta[4] = ""; 
switch($kolengde) {
	case 0: $ta[0] = " selected"; break;
	case 7: $ta[1] = " selected"; break;
	case 30: $ta[3] = " selected"; break;
	case 60: $ta[4] = " selected"; break;				
	default: $ta[2] = " selected";	
}
		
?>       

      <td><?php echo gettext("Max queuelength"); ?></td>
      <td align="center"><select name="kolengde" id="select">
          <option value="0"<?php echo $ta[0] . ">" . gettext("No queue"); ?></option>
          <option value="7"<?php echo $ta[1] . ">" . gettext("One week"); ?></option>
          <option value="14"<?php echo $ta[2] . ">" . gettext("Two weeks"); ?></option>          
          <option value="30"<?php echo $ta[3] . ">" . gettext("One month"); ?></option>
          <option value="60"<?php echo $ta[4] . ">" . gettext("Two months"); ?></option>          
        </select></td>
    </tr>    
    <tr>
      <td><input name="sms" type="checkbox" 
<?php 
	  if ($csms == 't') echo "checked";
?> value="1"><?php echo gettext("Access to SMS alert"); ?></td>
      <td align="right"><input type="submit" name="Submit" 
<?php
if ($subaction == 'endre') {
	echo 'value="' . gettext("Save changes") . '"';
} else {
	echo 'value="' . gettext("Add user") . '"';
}
?>
></td>
    </tr>
  </table>

</form>


</td></tr>
</table>

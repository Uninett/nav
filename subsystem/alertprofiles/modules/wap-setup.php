<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("WAP setup"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo "<p>";
echo gettext('Here you can setup and deactivate WAP access for your Alert profiles account.
Remember to keep your wap key secret. If compromised, you can generate a new key here or deactivate WAP access. When generating a new WAP key you have to remember to update your bookmark on your mobile telephone or PDA.');



$uid = session_get('uid');

if ($subaction == 'nykey') {
	$nk = chr (rand(0, 25) + ord('A')) .
		chr (rand(0, 25) + ord('A')) .
		rand(0, 9) . rand(0,9) .
		chr (rand(0, 25) + ord('A'));

	$dbh->settwapkey(session_get('uid'), $nk);
}
if ($subaction == 'slettkey') {
	$dbh->slettwapkey($uid);
}

;


$k = $dbh->hentwapkey($uid);
print "<h2>" . gettext("WAP key") . "</h2>";

if ($k[0] == null) {
	print "<p>" . gettext("You have no WAP key. One must be generated to access Alert Profiles from WAP.");
	print "<p>[ <a href=\"index.php?subaction=nykey\">" . gettext("Generate WAP key") . "</a> ]";	
} else {
	print "<p>" . gettext("Your WAP key is: ") ."<b>" . $k[0] . "</b>.";
	print "<p>" . gettext("You can now access Alert profiles from this WAP page :") . "<br>";
	print '<pre>http://' . $_SERVER['SERVER_NAME'] . '/wap/?k=' . $k[0] . '</pre>';

	print "<p>[ <a href=\"index.php?subaction=nykey\">" . gettext("Generate a new key") . "</a> | 
<a href=\"index.php?action=wap&subaction=slettkey\">" . gettext("Deactivate WAP access") . "</a> ]";

}
?>

</td></tr>
</table>

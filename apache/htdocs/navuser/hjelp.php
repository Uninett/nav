<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Hjelp"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
echo '<h1>Brukermanual</h1>';
echo '<p><img src="icons/pdf_icon.png" alt="PDF format">';
echo '[ <a href="documents/NAValert-manual.pdf">' . gettext("Last ned") . '</a> ] ' . gettext("brukermanual i PDF-format.");

?>

</td></tr>
</table>

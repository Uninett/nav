#!/usr/bin/perl

$footer = '/local/apache/vhtdocs/footer.html';

print "</td></tr></table>";

print "</td></tr>";

print "<tr><td colspan=2>";

open(FOOTER,$footer);
while (<FOOTER>)
{ print ; }
close(FOOTER);
 
print "</td></tr></table>";

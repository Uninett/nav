#!/usr/bin/perl

$menybrede = "100%";

$header     = '../vhtdocs/header.html';
$meny       = '../vhtdocs/meny.html';
$kontakt    = '../vhtdocs/kontakt.html';
$bruker     = '../vhtdocs/bruker.html';
$htpasswd   = '../htpasswd/.htpasswd-sroot';

open (HTPASSWD, $htpasswd) || die "Får ikke åpnet $htpasswd";
 
$user_data{''}{'omraade'} = 'aapen';
     while (<HTPASSWD>) {
            next if (/^\W/);
            ($user, $passord, $navn, $merknader, $omraade) = split(/\:/, $_);
            chomp ($user_data{$user}{'omraade'} = $omraade);
     }
 
close(HTPASSWD);


$remote_user = $ENV{'REMOTE_USER'};
$remote_host = $ENV{'REMOTE_HOST'};
$remote_ip = $ENV{'REMOTE_ADDR'};

print "<body bgcolor=\#ffffff text=\#000000>";

print "<table><tr><td bgcolor=\#ffffff colspan=2>";
 
open(TOPP,$header);
while (<TOPP>)
{ print ; }
close(TOPP);
print "</td></tr>";
 
print "<tr><td valign=top>";
 
print "
<table width=$menybrede bgcolor=\#000000 border=0 cellpadding=0 cellspacing=1>
 <tr><td>
   <table width=$menybrede cellspacing=1 border=0 cellpadding=2 bgcolor=\#e6e6e6>
   <tr><td bgcolor=\#486591><font color=\#ffffff>
        <strong><font color=\#fefefe\>Brukerinfo
";

#print "<a href=https://www.nav.ntnu.no/restricted/>Logg inn</a>
print "<a href=../shtdocs/>Logg inn</a>
<a href=/doc/hjelp.html>Hjelp</a>" if
(lc($user_data{$remote_user}{'omraade'}) eq 'aapen');
print "<a href=/sec/>Logg inn</a>" if (lc($user_data{$remote_user}{'omraade'}) eq 'begrenset');
 
print "
</font></strong></font>
       </td>
   </tr>
   </table>
   <table width=$menybrede cellspacing=1 border=0 cellpadding=7 bgcolor=\#fefefe>
   <tr><td bgcolor=\#e6e6e6>
         <table>
         <tr><td><b>BRUKER:</td><td>$remote_user</td></tr>
         <tr><td><b>ADGANG:</td><td>$user_data{$remote_user}{omraade}</td></tr>
         <tr><td><b>IP:</td><td>$remote_ip</td></tr>
         </table>";

print "<p>";
unless ($user_data{$remote_user}{omraade} eq 'aapen')
{
    open(BRUKER,$bruker);
    while (<BRUKER>)
    { print ; }
    close(BRUKER);
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
<table width=$menybrede bgcolor=\#000000 border=0 cellpadding=0 cellspacing=1>
 <tr><td>
  <table width=$menybrede cellspacing=1 border=0 cellpadding=2 bgcolor=\#e6e6e6>
    <tr><td bgcolor=\#486591><font color=\#ffffff>
       <strong><font color=\#fefefe\>Linker</font></strong>      </font>
     </td></tr>
  </table>
  <table width=$menybrede cellspacing=1 border=0 cellpadding=7 bgcolor=\#fefefe>
    <tr><td bgcolor=\#e6e6e6>
";
 
open(MENY,$meny);
while (<MENY>)
{ print ; }
close(MENY);
 
print "</td></tr></table></td></tr></table><p>";
 
print "
<table width=$menybrede bgcolor=\#000000 border=0 cellpadding=0 cellspacing=1>
 <tr><td>
   <table width=$menybrede cellspacing=1 border=0 cellpadding=2 bgcolor=\#e6e6e6>
    <tr><td bgcolor=\#486591><font color=\#ffffff>
       <strong><font color=\#fefefe\>Kontakt Nettgruppen</font></strong>      </font>
     </td></tr></table>
   <table width=$menybrede cellspacing=1 border=0 cellpadding=7 bgcolor=\#fefefe>
   <tr><td bgcolor=\#e6e6e6>
";
 
open(KONTAKT,$kontakt);
while (<KONTAKT>)
{ print ; }
close(KONTAKT);
 
print "</td></tr></table></td></tr></table>";
 
 
print "</td><td valign=top bgcolor=\#ffffff>";

print "<table border=0 cellpadding=10 cellspacing=1> <tr><td>";








#$remote_user = $ENV{'REMOTE_USER'}; 

#$user='grohi';

#print "Bruker er $user<br>";
#print "Remote user er $remote_user<br>";


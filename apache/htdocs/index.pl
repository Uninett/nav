#!/usr/bin/perl -w

use CGI qw(:standard);

print header;
print start_html(NAV);

$vhtdocs = '/usr/local/nav/navme/apache/vhtdocs';
$htpasswd = '/usr/local/nav/navme/apache/htpasswd';

$navstart = "$vhtdocs/navstart.pl";
$navslutt = "$vhtdocs/navslutt.pl";

$public     = "$vhtdocs/public.html";
$restricted = "$vhtdocs/restricted.html";
$secret     = "$vhtdocs/secret.html";
$passwdfil = "$htpasswd/.htpasswd-sroot";


$remote_user = $ENV{'REMOTE_USER'};
###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
print `$navstart $remote_user`;
###########################################

open (HTPASSWD, $passwdfil) || die "Får ikke åpnet $passwdfil";
 
$user_data{''}{'omraade'} = 'aapen';
while (<HTPASSWD>) 
{
    next if (/^\W/);
    ($user, $passord, $navn, $merknader, $omraade) = split(/\:/, $_);
    chomp ($user_data{$user}{'omraade'} = $omraade);
}	    
close(HTPASSWD);

open(PUBLIC,$public);
while (<PUBLIC>)
{ print ; }
close(PUBLIC);
 
if (lc($user_data{$remote_user}{'omraade'}) eq 'begrenset')
{
   open(RESTRICTED,$restricted);
   while (<RESTRICTED>)
   { print ; }
   close(RESTRICTED);
}
 
if (lc($user_data{$remote_user}{'omraade'}) eq 'intern')
{
   open(RESTRICTED,$restricted);
   while (<RESTRICTED>)
   { print ; }
   close(RESTRICTED);
 
   open(SECRET,$secret);
   while (<SECRET>)
   { print ; }
   close(SECRET);
}

###########################################
# Kjører filen navslutt, og skriver "print-linjene" til web
print `$navslutt`;
###########################################

print end_html;


#!/usr/bin/perl -w

use CGI qw(:standard);

print header;
print start_html(NAV);

$navstart = '/local/apache/htdocs/public/perl/navstart.pl';
$navslutt = '/local/apache/htdocs/public/perl/navslutt.pl';

$public     = '../vhtdocs/public.html';
$restricted = '../vhtdocs/restricted.html';
$secret     = '../vhtdocs/secret.html';
$htpasswd = "/usr/local/apache/htpasswd/.htpasswd-sroot";

###########################################
# Kjører filen navstart, og skriver "print-linjene" til web
print `$navstart`;
###########################################

open (HTPASSWD, $htpasswd) || die "Får ikke åpnet $htpasswd";
 
$user_data{''}{'omraade'} = 'aapen';
while (<HTPASSWD>) 
{
    next if (/^\W/);
    ($user, $passord, $navn, $merknader, $omraade) = split(/\:/, $_);
    chomp ($user_data{$user}{'omraade'} = $omraade);
}	    
close(HTPASSWD);

$remote_user = $ENV{'REMOTE_USER'};

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


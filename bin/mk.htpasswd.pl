#!/usr/bin/perl

use strict;

#denne skal hentes i fra den generelle config
my $nav_sti = "/usr/local/nav";

my $apache_htpasswd = "$nav_sti/local/apache/htpasswd";
my $nav_htpasswd_conf = "$nav_sti/local/etc/htpasswd";

# Må oppdateres etter instalasjonen
my $brukerdb = "$nav_htpasswd_conf/passwd";


my $intern_userlist = "$nav_htpasswd_conf/intern_user";
my $stat_userlist  = "$nav_htpasswd_conf/stat_user";

my $htpasswd_sroot = "$apache_htpasswd/.htpasswd-sroot";
my $htpasswd_sec = "$apache_htpasswd/.htpasswd-sec";
my $htpasswd_res = "$apache_htpasswd/.htpasswd-res";



my (%sroot, %sec, %res);
my (%internlist);
my ($user, $passwd, $navn, $info, $adgang);
my ($key, $dummy, $i);


open (INTERN_FIL, "<$intern_userlist") || die "Får ikke åpnet filen med de interne brukerene: $intern_userlist $!\n";

  while (<INTERN_FIL>) {
    next if (/^\W/);
   
   chomp ($_); 
   $internlist{$_} = $_;
  }
close (INTERN_FIL);


open (STAT_FIL, "<$stat_userlist") || die "Får ikke åpnet filen med de statiske brukerene: $stat_userlist $!\n";

  while (<STAT_FIL>) {
    
    next if (/^\W/);

    ($user, $passwd, $navn, $info, $adgang) = split(/:/, $_);

    chomp($adgang);
    
    if (lc($adgang) eq "intern") {
      $sec{$user}{passwd} = $passwd;
      $sec{$user}{navn}   = $navn;
      $sec{$user}{info}   = $info;
      $sec{$user}{adgang} = $adgang;
    }

    elsif (lc($adgang) eq 'begrenset') {
      $res{$user}{passwd} = $passwd;
      $res{$user}{navn}   = $navn;
      $res{$user}{info}   = $info;
      $res{$user}{adgang} = $adgang;
    }

    # NTNU propritært
    elsif (lc($adgang) eq 'nettass') {
	$sby{$user}{passwd} = $passwd;
	$sby{$user}{navn}   = $navn;
	$sby{$user}{info}   = $info;
	$sby{$user}{adgang} = 'begrenset';  
    }

    else {
      $sroot{$user}{passwd} = $passwd;
      $sroot{$user}{navn}   = $navn;
      $sroot{$user}{info}   = $info;
      $sroot{$user}{adgang} = 'aapen';
    }

  }

close (STAT_FIL);


open (DB_FIL, "<$brukerdb") || die "Får ikke åpnet filen med brukerene: $brukerdb $!\n";

  while (<DB_FIL>) {
    
    next if (/^\W/);

    ($user, $passwd, $dummy, $dummy, $navn, $dummy) = split(/:/, $_);

    if ($internlist{$user} eq $user)  {

	delete $sroot{$user} if ($sroot{$user});
	delete $res{$user}   if ($res{$user});
	delete $sby{$user}   if ($sby{$user});

	$sec{$user}{passwd} = $passwd;
	$sec{$user}{navn}   = $navn;
	$sec{$user}{info}   = 'autogenerert';
	$sec{$user}{adgang} = 'intern';
    }

    else {

	delete $sroot{$user} if ($sroot{$user});
	delete $sec{$user}   if ($sec{$user});
	delete $sby{$user}   if ($sby{$user});

	$res{$user}{passwd} = $passwd;
	$res{$user}{navn}   = $navn;
	$res{$user}{info}   = 'autogenerert';
	$res{$user}{adgang} = 'begrenset';
    }

  }

close (DB_FIL);



open (SROOT, ">$htpasswd_sroot") || die "Får ikke åpnet filen: $htpasswd_sroot $!\n";

  print SROOT "# AApen\n";
  print SROOT ":5Hm7db4naYRDg:Bruker uten passord::aapen\n";

  foreach $key (keys %sroot) {
    
    print SROOT "$key:$sroot{$key}{passwd}:$sroot{$key}{navn}:$sroot{$key}{info}:$sroot{$key}{adgang}\n";
  }

  print SROOT "\n# Begrenset\n";

  foreach $key (keys %res) {

    print SROOT "$key:$res{$key}{passwd}:$res{$key}{navn}:$res{$key}{info}:$res{$key}{adgang}\n";
  }

  print SROOT "\n# Intern\n";

  foreach $key (keys %sec) {

    print SROOT "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }

close (SROOT);




open (RES, ">$htpasswd_res") || die "Får ikke åpnet filen: $htpasswd_res $!\n";

  print RES "# Begrenset\n";

  foreach $key (keys %res) {

    print RES "$key:$res{$key}{passwd}:$res{$key}{navn}:$res{$key}{info}:$res{$key}{adgang}\n";
  }


  print RES "\n# Intern\n";

  foreach $key (keys %sec) {

    print RES "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }

close (RES);



open (SEC, ">$htpasswd_sec") || die "Får ikke åpnet filen: $htpasswd_sec $!\n";

  print SEC "# Intern\n";

  foreach $key (keys %sec) {

    print SEC "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }

close (SEC);

1;

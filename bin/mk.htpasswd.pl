#!/usr/bin/perl

use strict;

my $intern_userlist = "/usr/local/apache/htpasswd/intern_user";
my $nettass_userlist = "/usr/local/apache/htpasswd/nettass_user"; 
my $stat_userlist  = "/usr/local/apache/htpasswd/stat_user";
my $bdb_userlist = "/usr/local/etc/passwd.bdb.nettinfo";

my $htpasswd_sroot = "/usr/local/apache/htpasswd/.htpasswd-sroot";
my $htpasswd_sec = "/usr/local/apache/htpasswd/.htpasswd-sec";
my $htpasswd_res = "/usr/local/apache/htpasswd/.htpasswd-res";
my $htpasswd_sby = "/usr/local/apache/htpasswd/.htpasswd-sby"; 


my (%sroot, %sec, %res, %sby);
my (%internlist, %nettasslist);
my ($user, $passwd, $navn, $info, $adgang);
my ($key, $dummy, $i);


open (INTERN_FIL, "<$intern_userlist") || die "Får ikke åpnet filen med de interne brukerene: $intern_userlist $!\n";

  while (<INTERN_FIL>) {
    next if (/^\W/);
   
   chomp ($_); 
   $internlist{$_} = $_;
  }
close (INTERN_FIL);



open (NETTASS_FIL, "<$nettass_userlist") || die "F?r ikke ?pnet filen med de interne brukerene: $nettass_userlist $!\n";
 
while (<NETTASS_FIL>) {
    next if (/^\W/);
 
    chomp ($_);
    $nettasslist{$_} = $_;
}
close (NETTASS_FIL);  



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

    elsif (lc($adgang) eq 'nettass') {
	$sby{$user}{passwd} = $passwd;
	$sby{$user}{navn}   = $navn;
	$sby{$user}{info}   = $info;
	$sby{$user}{adgang} = $adgang;  
    }

    else {
      $sroot{$user}{passwd} = $passwd;
      $sroot{$user}{navn}   = $navn;
      $sroot{$user}{info}   = $info;
      $sroot{$user}{adgang} = 'aapen';
    }

  }

close (STAT_FIL);


open (BDB_FIL, "<$bdb_userlist") || die "Får ikke åpnet filen med bdb-brukerene: $bdb_userlist $!\n";

  while (<BDB_FIL>) {
    
    next if (/^\W/);

    ($user, $passwd, $dummy, $dummy, $navn, $dummy) = split(/:/, $_);

    if ($internlist{$user} eq $user)  {

	delete $sroot{$user} if ($sroot{$user});
	delete $res{$user}   if ($res{$user});
	delete $sby{$user}   if ($sby{$user});

	$sec{$user}{passwd} = $passwd;
	$sec{$user}{navn}   = $navn;
	$sec{$user}{info}   = 'bdb nettinfo';
	$sec{$user}{adgang} = 'intern';
    }

    elsif ($nettasslist{$user} eq $user) {
	
	delete $sroot{$user} if ($sroot{$user});
	delete $sec{$user}   if ($sec{$user});
	delete $res{$user}   if ($res{$user});
 
	$sby{$user}{passwd} = $passwd;
	$sby{$user}{navn}   = $navn;
	$sby{$user}{info}   = 'bdb nettinfo';
	$sby{$user}{adgang} = 'nettass';
    }                                    

    else {

	delete $sroot{$user} if ($sroot{$user});
	delete $sec{$user}   if ($sec{$user});
	delete $sby{$user}   if ($sby{$user});

	$res{$user}{passwd} = $passwd;
	$res{$user}{navn}   = $navn;
	$res{$user}{info}   = 'bdb nettinfo';
	$res{$user}{adgang} = 'begrenset';
    }

  }

close (BDB_FIL);



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

  print SROOT "\n# Nettass\n";
 
  foreach $key (keys %sby) {
 
    print SROOT "$key:$sby{$key}{passwd}:$sby{$key}{navn}:$sby{$key}{info}:begrenset\n";
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


  print RES "\n# Nettass\n";
 
  foreach $key (keys %sby) {
 
    print RES "$key:$sby{$key}{passwd}:$sby{$key}{navn}:$sby{$key}{info}:begrenset\n";
  }    


  print RES "\n# Intern\n";

  foreach $key (keys %sec) {

    print RES "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }

close (RES);



open (SBY, ">$htpasswd_sby") || die "F?r ikke ?pnet filen: $htpasswd_sby $!\n";

  print SBY "# Nettass\n";
 
  foreach $key (keys %sby) {
 
    print SBY "$key:$sby{$key}{passwd}:$sby{$key}{navn}:$sby{$key}{info}:begrenset\n";
  } 

 
  print SBY "\n# Intern\n";
 
  foreach $key (keys %sec) {
 
    print SBY "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }
 
close (SBY);  



open (SEC, ">$htpasswd_sec") || die "Får ikke åpnet filen: $htpasswd_sec $!\n";

  print SEC "# Intern\n";

  foreach $key (keys %sec) {

    print SEC "$key:$sec{$key}{passwd}:$sec{$key}{navn}:$sec{$key}{info}:$sec{$key}{adgang}\n";
  }

close (SEC);

1;



#!/usr/bin/perl

#################################################
# Dette scriptet henter bokser fra manage.boks
# Går så ut og spør om diverse info om boksene.
# Legges i manage.module og manage.mem
#
# NB! 3com-stacker sees på som en boks med flere moduler.
# Antall i Stack finnes ved å telle antall moduler som har
# samme boksid
#
##################################################


use SNMP_util;
use Pg;
use strict;

require "/usr/local/nav/navme/etc/conf/path.pl";
my $lib = &lib();
require "$lib/snmplib.pl";
require "$lib/database.pl";

my %boks = ();
my %module = ();
my %module_new = ();
my %boksinfo =();
my %boksinfo_new = ();
my %mib;
my %mem;
my %flash;
my %mf_db;  # memory og flash fra databasen

my %cat6sw = (); # ID til bokser med main_sw fra 5.X og oppover legges i denne. Spesialbehandling i &get_catsw

my %catswModulType;

my $conn = &db_get("get_boksdata"); 

my $sql = "SELECT boksid,ip,ro,typegruppe,watch FROM boks join type using (typeid)";

my $res = db_select($conn,$sql);

while (my @line = $res->fetchrow)
{    
    $boks{$line[0]}{ip}      = $line[1];
    $boks{$line[0]}{ro}      = $line[2];
    $boks{$line[0]}{type}    = $line[3];
    $boks{$line[0]}{watch}   = $line[4];
#    print "@line\n";
}


$sql = "SELECT boksid,main_sw,serial FROM boksinfo";
$res = db_select($conn,$sql);

while (my @line = $res->fetchrow)
{ 
    $boksinfo{$line[0]}{main_sw} = $line[1];
    $boksinfo{$line[0]}{serial}  = $line[2];
}

$sql = "SELECT moduleid,boksid,modulenumber,model,descr,serial,hw,sw,ports,portsUp FROM module";

$res = db_select($conn,$sql);

while (my @line = $res->fetchrow)
{
    $module{$line[1]}{$line[2]}{id}      = $line[0];
    $module{$line[1]}{$line[2]}{model}   = $line[3];
    $module{$line[1]}{$line[2]}{descr}   = $line[4];   
    $module{$line[1]}{$line[2]}{serial}  = $line[5];
    $module{$line[1]}{$line[2]}{hw}      = $line[6];
    $module{$line[1]}{$line[2]}{sw}      = $line[7];
    $module{$line[1]}{$line[2]}{ports}   = $line[8];
    $module{$line[1]}{$line[2]}{portsUp} = $line[9];
    #print "@line\n";
}

$sql = "SELECT memid,boksid,memtype,device,size,used FROM mem";

$res = db_select($conn,$sql);

while (my @line = $res->fetchrow)
{
    #       boksid    memtype   device
    $mf_db{$line[1]}{$line[2]}{$line[3]}{memid} = $line[0]; 
    $mf_db{$line[1]}{$line[2]}{$line[3]}{size}  = $line[4]; 
    $mf_db{$line[1]}{$line[2]}{$line[3]}{used}  = $line[5]; 

    # memtype er flash eller memory

}

my $id;


# Definerer mibs inn i hash(er)
&mibs;


foreach $id (keys %boks)
{

    unless ($boks{$id}{watch} eq 't')
    {
	
#	if ($boks{$id}{ip} eq '129.241.76.147')
#	{

#	    print "$boks{$id}{ip}\n";
	    
	    &get_boksinfo($id);
	    
	    &get_cgw($id) if ($boks{$id}{type} eq 'cgw');
	    &get_3ss($id) if ($boks{$id}{type} eq '3ss');
	    &get_catsw($id) if ($boks{$id}{type} eq 'cat-sw');
            &get_hpsw($id) if ($boks{$id}{type} eq 'hpsw');	    
#	&get_iossw($id) if ($boks{$id}{type} eq 'ios-sw');
	    
            unless (($boks{$id}{type} =~ '3ss') or ($boks{$id}{type} =~ 'hpsw')) {
		    &get_mem($id);
		    &get_flash($id);
	    }
#	}
	
    }
    
}

my $num;
my @felt = ('model','descr','serial','hw','sw','ports','portsUp');
my $felt;

#foreach $id (keys %module_new)
#{
#    foreach $num (keys %{$module_new{$id}})
#    {
#	foreach $felt (@felt)
#	{
#	    print "MODNEW: $id\t$num\t$felt\t$module_new{$id}{$num}{$felt}\n";
#	}
#    }
#}


# Oppdater boksinfo

foreach $id (keys %boksinfo)
{
    if ($boks{$id}{watch} eq 't')
    {
	delete $boksinfo_new{$id};
    }
    else
    {	
	# main_sw
	unless ($boksinfo{$id}{main_sw} eq $boksinfo_new{$id}{main_sw})
	{
	    $sql = "UPDATE boksinfo SET main_sw=\'$boksinfo_new{$id}{main_sw}\' WHERE boksid = \'$id\'";
	    db_execute($conn,$sql);
	}
	    
	# serial
	unless ($boksinfo{$id}{serial} eq $boksinfo_new{$id}{serial})
	{
	    $sql = "UPDATE boksinfo SET serial=\'$boksinfo_new{$id}{serial}\' WHERE boksid = \'$id\'";
	    db_execute($conn,$sql);
	}
	
	delete $boksinfo_new{$id};
    }
}

# Nye innslag i boksinfo

foreach $id (keys %boksinfo_new)
{
    if ($boksinfo_new{$id}{main_sw}||$boksinfo_new{$id}{serial})
    {
	$sql = "INSERT INTO boksinfo (boksid,main_sw,serial) VALUES (\'$id\',\'$boksinfo_new{$id}{main_sw}\',\'$boksinfo_new{$id}{serial}\')";
	db_execute($conn,$sql);
    }
}


foreach $id (keys %module)
{
    if ($boks{$id}{watch} eq 't')
    {
	delete $module{$id};
    }
    else
    {	
	foreach $num (keys %{$module{$id}})
	{
	    foreach $felt (@felt)
	    {

#		print "$id\t$num\t$felt\t$module_new{$id}{$num}{$felt}\n";
		unless ($module{$id}{$num}{$felt} eq $module_new{$id}{$num}{$felt})
		{
		    $sql = "UPDATE module SET $felt=\'$module_new{$id}{$num}{$felt}\' WHERE moduleid = \'$module{$id}{$num}{id}\'";
		    db_execute($conn,$sql);
		}
	    }
	    delete $module{$id}{$num};
	    delete $module_new{$id}{$num};
	}	
    }

}
 

# Slett fra db det som er igjen i $module

foreach $id (keys %module)
{
    foreach $num (keys %{$module{$id}})
    {
	$sql = "DELETE FROM module WHERE moduleid=\'$module{$id}{$num}{id}\'";
	db_execute($conn,$sql);
    }
}


# Legg inn i db det som er igjen i $module_new

foreach $id (keys %module_new)
{
    foreach $num (keys %{$module_new{$id}})
    {
	$sql = "INSERT INTO module (boksid,modulenumber,model,descr,serial,hw,sw,ports,portsUp) VALUES (\'$id\',\'$num\',\'$module_new{$id}{$num}{model}\',\'$module_new{$id}{$num}{descr}\',\'$module_new{$id}{$num}{serial}\',\'$module_new{$id}{$num}{hw}\',\'$module_new{$id}{$num}{sw}\',\'$module_new{$id}{$num}{ports}\',\'$module_new{$id}{$num}{portsUp}\')";
	    db_execute($conn,$sql);
	
    }
}


# Oppdater mem-tabellen

# Samlet inn:  $mem{boksid}{name}{used|size} 
#           og $flash{boksid}{name}{size}
# Fra databasen: $mf_db{boksid}{memtype}{device}{memid|size|used}

my $dev;
my $memtype;

foreach $id (keys %mf_db)
{
    if ($boks{$id}{watch} eq 't')
    {
	delete $mf_db{$id};
    }
    else
    {	
	# memory
	foreach $dev (keys %{$mf_db{$id}{memory}})
	{
	    unless ($mf_db{$id}{memory}{$dev}{size} eq $mem{$id}{$dev}{size})
	    {
		$sql = "UPDATE mem SET size=\'$mem{$id}{$dev}{size}\' WHERE memid=\'$mf_db{$id}{memory}{$dev}{memid}\'";
#		print "$sql\n";
		db_execute($conn,$sql);

	    }
	    unless ($mf_db{$id}{memory}{$dev}{used} eq $mem{$id}{$dev}{used})
	    {
		$sql = "UPDATE mem SET used=\'$mem{$id}{$dev}{used}\' WHERE memid=\'$mf_db{$id}{memory}{$dev}{memid}\'";
#		print "$sql\n";
		db_execute($conn,$sql);
	    }

	    delete $mf_db{$id}{memory}{$dev};
	    delete $mem{$id}{$dev};

	}

	# flash

	foreach $dev (keys %{$mf_db{$id}{flash}})
	{
	    unless ($mf_db{$id}{flash}{$dev}{size} eq $flash{$id}{$dev}{size})
	    {
		$sql = "UPDATE mem SET size=\'$flash{$id}{$dev}{size}\' WHERE memid=\'$mf_db{$id}{flash}{$dev}{memid}\'";
#		print "$sql\n";
		db_execute($conn,$sql);
	    }

            unless ($mf_db{$id}{flash}{$dev}{used} eq $flash{$id}{$dev}{used})
            {
                $sql = "UPDATE mem SET used=\'$flash{$id}{$dev}{used}\' WHERE memid=\'$mf_db{$id}{flash}{$dev}{memid}\'";
#               print "$sql\n";
                db_execute($conn,$sql);
            }

	    delete $mf_db{$id}{flash}{$dev};
	    delete $flash{$id}{$dev};
	}
	
    }
}

# Nye innslag i mem-tabellen

# memory
foreach $id (keys %mem)
{
    foreach $dev (keys %{$mem{$id}})
    {
	$sql = "INSERT INTO mem (boksid,memtype,device,size,used) VALUES (\'$id\',\'memory\',\'$dev\',\'$mem{$id}{$dev}{size}\',\'$mem{$id}{$dev}{used}\')";
	db_execute($conn,$sql);
#	print "$sql\n";
    }
}

# flash

foreach $id (keys %flash)
{
    foreach $dev (keys %{$flash{$id}})
    {
	$sql = "INSERT INTO mem (boksid,memtype,device,size,used) VALUES (\'$id\',\'flash\',\'$dev\',\'$flash{$id}{$dev}{size}\',\'$flash{$id}{$dev}{size}\')";
#	print "$sql\n";
	db_execute($conn,$sql);
    }
}

# Slette gamle innslag - dvs. det som erigjen i %mf_db

foreach $id (keys %mf_db)
{
    foreach $memtype (keys %{$mf_db{$id}})
    {
	foreach $dev (keys %{$mf_db{$id}{$memtype}})
	{	
	    $sql = "DELETE FROM mem WHERE memid=\'$mf_db{$id}{$memtype}{$dev}{memid}\'";
#	    print "$sql\n";    
	    db_execute($conn,$sql);
	}
    }
}



###########################################

sub get_3ss
{
    my $id_ = $_[0];

#    print "$boks{$id_}{ip}\t$boks{$id_}{type}\n";

#    walk tar inn ($boksid,$var), gjør snmpwalk 
#    og legger inn data i $module{$id_}{unit}{$var}
#    $var er her modul,descr,osv.

    &walk($id_,'model');
    &walk($id_,'descr');
    &walk($id_,'serial');
    &walk($id_,'hw');
    &walk($id_,'sw');

}

###########################################

sub get_cgw
{
    my $id_ = $_[0];
    
#    print "$boks{$id_}{ip}\t$boks{$id_}{type}\n";
    
#    walk tar inn ($boksid,$var), gjør snmpwalk 
#    og legger inn data i $module{$id_}{unit}{$var}
#    $var er her modul,descr,osv.
    
    &walk($id_,'model');
    &walk($id_,'descr');
    &walk($id_,'serial');
    &walk($id_,'hw');
    &walk($id_,'sw');
    
}

#############################################

sub get_catsw
{
    my $id_ = $_[0];

#    print "$boks{$id_}{ip}\t$boks{$id_}{type}\n";

#    walk tar inn ($boksid,$var), gjør snmpwalk 
#    og legger inn data i $module{$id_}{unit}{$var}
#    $var er her modul,descr,osv.

    &walk($id_,'model');
#    &walk($id_,'descr');
    &walk($id_,'serial');
    &walk($id_,'hw');
    &walk($id_,'sw');
    &walk($id_,'ports');

    my @temp;
    my $key;
    my $number;
    my $temp;

#    print "$mib{$boks{$id_}{type}}{portsUp}\n";
    
    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{portsUp}");
  
#    print "@temp\n";

    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);

#	my $hexnum = oct($temp);

#	print "$boks{$id_}{ip}\t$number\t$temp\t$hexnum\n";

#	$module_new{$id_}{$number}{$var} = $temp; 
#	print "$var: $number\t$temp\n";	
    }

    my $modtype;
    my %modtype;
    my $modnr;
    my %modnr;


    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{modnr}");
    
    foreach $key (@temp)
    {
	($number,$modnr) = split(/:/,$key);
	$modnr{$number} = $modnr;
    }
    
    
    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{modtype}");
    foreach $key (@temp)
    {
#	print "$key\n";
	($number,$modtype) = split(/:/,$key);
	$modtype{$number} = $modtype;
    }
    
    foreach $key (keys %modtype)
    {
	
	unless ($cat6sw{$id_})
	{	   
	    if ($modnr{$key})
	    {
		$module_new{$id_}{$modnr{$key}}{descr} = $modtype{$key};
	    }
	}	
	else # main_sw er 6.X eller høyere
	{
	    if ($modnr{$key} =~ /^module/)
	    {
		$_ = $modnr{$key};
		s/module//;
		s/\s+//;
		$modnr{$key} = $_;

	#	print "modul $modnr{$key}\t$modtype{$key}\n";

		$module_new{$id_}{$modnr{$key}}{descr} = $modtype{$key};
	    }
	}
    }
}



###########################################

sub get_hpsw
{
    my $id_ = $_[0];
    my (@ais, $ais, $unit);
    
    
    # Finn antall unitter i stakken
    @ais = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{'ais'}");
    $ais =$#ais;
    if ($ais eq '-1') {$ais = 0;}
    
    for ($unit = 0; $unit < $ais+1; $unit++) {
        &hpwalk($id_,$unit,'model');
	&hpwalk($id_,$unit,'serial');
        &hpwalk($id_,$unit,'descr');
	&hpwalk($id_,$unit,'hw');
	&hpwalk($id_,$unit,'sw');
	&hpwalk($id_,$unit,'size');
	&hpwalk($id_,$unit,'used');
    }	    

}


#############################################

sub get_mem
{
    my $id_ = $_[0];
    my @temp;
    my $key;
    my $number;
    my $temp;
    my %id2name;

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{mem}{name}");
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
#	print "$key\n"; 
	$id2name{$number} = $temp;
    }

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{mem}{used}");
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
	$mem{$id_}{$id2name{$number}}{used} = $temp;
#	print "$key\n"; 
    }

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{mem}{free}");
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
	$mem{$id_}{$id2name{$number}}{free} = $temp;
	$mem{$id_}{$id2name{$number}}{size} = $temp + $mem{$id_}{$id2name{$number}}{used};
#	print "$key\n"; 
    }

#    foreach $key (keys %{$mem{$id_}})
#    {
#	print "memory\t$key\t$mem{$id_}{$key}{used}\t$mem{$id_}{$key}{free}\t$mem{$id_}{$key}{size}\n";
#    }

}

#############################################

sub get_flash
{
    my $id_ = $_[0];
    my @temp;
    my $key;
    my $number;
    my $temp;
    my %id2name;

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{flash}{name}");
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
#	print "$key\n"; 
	$id2name{$number} = $temp;
    }

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{flash}{size}");
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
	$flash{$id_}{$id2name{$number}}{size} = $temp;
#	print "$key\n"; 
    }

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{flash}{free}");
    foreach $key (@temp)
    {
        ($number,$temp) = split(/:/,$key);
        $flash{$id_}{$id2name{$number}}{used} = $flash{$id_}{$id2name{$number}}{size} - $temp;
#       print "$key\n";

#	print "used: $flash{$id_}{$id2name{$number}}{used}\n";

    }




#    foreach $key (keys %{$flash{$id_}})
#    {
#	print "flash\t$key\t$flash{$id_}{$key}{size}\n";
#    }
}



#############################################

sub get_boksinfo
{
    my $id_ = $_[0];
    my @temp;
    my $key;
    my ($temp1,$temp2,$temp3);

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{boksinfo}{sysDescr}");
    if ($temp[0])
    {
	
	($temp1,$temp2,$temp3) = split(/Version|Copyright/,$temp[0]);
	
	($temp2,$temp3) = split(/,/,$temp2);
	
	chomp($temp2);
	
	$_ = $temp2;
	s/\s+//g;
	$temp2 = $_;

	$boksinfo_new{$id_}{main_sw} = $temp2;

	($temp1,$temp3) = split(/\./,$temp2);
	if ($temp1 gt 4)
	{
	    $cat6sw{$id_}++;
	}
#	print "$boks{$id_}{ip}\t*$temp2*\n";
    }

    @temp = ();
	
    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{boksinfo}{serial}");
    
    if ($temp[0])
    {
	($temp1,$temp2) = split(/:/,$temp[0]);
	chomp($temp2);
	$boksinfo_new{$id_}{serial} = $temp2; 
    }
}

#############################################


sub walk
{
    my $id_ = $_[0];
    my $var = $_[1];

    my @temp;
    my $key;
    my $number;
    my $temp;

    @temp = &snmpwalk("$boks{$id_}{ro}\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{$var}");  
    foreach $key (@temp)
    {
	($number,$temp) = split(/:/,$key);
	$module_new{$id_}{$number}{$var} = $temp; 
#	print "$var: $number\t$temp\n";	
    }
}

#############################################


#############################################


sub hpwalk
{
	my $id_ = $_[0];
	my $unit_ = $_[1];
	my $var = $_[2];

	my @temp;
	my $key;
	my $number;
	my $temp;
	my $ro_;

	if ($unit_ eq '0') {$ro_ = $boks{$id_}{ro};}
	else { $ro_ = $boks{$id_}{ro}.'@sw'.$unit_;}
	

	(@temp) = &snmpget("$ro_\@$boks{$id_}{ip}","$mib{$boks{$id_}{type}}{$var}");
	chomp($temp[0]);
	foreach $key (@temp)
	{
		unless (($var =~ 'used') or ($var =~ 'size')) {
			$module_new{$id_}{$unit_}{$var} = $temp[0];
#			print "$id_\t$var: $unit_\t$temp[0]\n";
		}
		
		else {
			$mem{$id_}{'Unit'.$unit_}{$var} = $temp[0];	
		}
	}
}

#############################################


sub mibs
{    


# model,descr,serial,hw,sw

# typegruppe 3ss
    $mib{'3ss'}{mac} = '.1.3.6.1.4.1.43.10.27.1.1.1.2';
    $mib{'3ss'}{model} = '.1.3.6.1.4.1.43.10.27.1.1.1.19';
    $mib{'3ss'}{descr} = '.1.3.6.1.4.1.43.10.27.1.1.1.5';
    $mib{'3ss'}{serial} = '.1.3.6.1.4.1.43.10.27.1.1.1.13';
    $mib{'3ss'}{hw} = '.1.3.6.1.4.1.43.10.27.1.1.1.11';
    $mib{'3ss'}{sw} = '.1.3.6.1.4.1.43.10.27.1.1.1.12';


# typegruppe cat-sw
    $mib{'cat-sw'}{model} = '.1.3.6.1.4.1.9.5.1.3.1.1.17';
    $mib{'cat-sw'}{descr} = '.1.3.6.1.4.1.9.5.1.3.1.1.13';
    $mib{'cat-sw'}{serial} = '.1.3.6.1.4.1.9.5.1.3.1.1.26';
    $mib{'cat-sw'}{hw} = '.1.3.6.1.4.1.9.5.1.3.1.1.18';
    $mib{'cat-sw'}{sw} = '.1.3.6.1.4.1.9.5.1.3.1.1.20';
    $mib{'cat-sw'}{ports} = '.1.3.6.1.4.1.9.5.1.3.1.1.14';
    $mib{'cat-sw'}{portsUp} = '.1.3.6.1.4.1.9.5.1.3.1.1.15';
    $mib{'cat-sw'}{modnr} = '.1.3.6.1.2.1.47.1.1.1.1.7';
    $mib{'cat-sw'}{modtype} = '.1.3.6.1.2.1.47.1.1.1.1.2'; 


# typegruppe ios-sw
    $mib{'ios-sw'}{model} = '';
    $mib{'ios-sw'}{descr} = '';
    $mib{'ios-sw'}{serial} = '';
    $mib{'ios-sw'}{hw} = '';
    $mib{'ios-sw'}{sw} = '';

# typegruppe cgw
    $mib{'cgw'}{model} = '.1.3.6.1.4.1.9.3.6.11.1.2';
    $mib{'cgw'}{descr} = '.1.3.6.1.4.1.9.3.6.11.1.3';
    $mib{'cgw'}{serial} = '.1.3.6.1.4.1.9.3.6.11.1.4';
    $mib{'cgw'}{hw} = '.1.3.6.1.4.1.9.3.6.11.1.5';
    $mib{'cgw'}{sw} = '.1.3.6.1.4.1.9.3.6.11.1.6';


# typegruppe hpsw
    $mib{'hpsw'}{mac} = '.1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.2.0';
    $mib{'hpsw'}{model} = '.1.3.6.1.4.1.11.2.36.1.1.2.5.0';
    $mib{'hpsw'}{descr} = '.1.3.6.1.4.1.11.2.36.1.1.5.1.1.9.1';
    $mib{'hpsw'}{serial} = '.1.3.6.1.2.1.47.1.1.1.1.11.1';
    $mib{'hpsw'}{hw} = '.1.3.6.1.4.1.11.2.14.11.5.1.1.4.0';
    $mib{'hpsw'}{sw} = '.1.3.6.1.4.1.11.2.14.11.5.1.1.3.0';
    $mib{'hpsw'}{ais} = '.1.3.6.1.4.1.11.2.14.11.5.1.10.4.1.1';
    $mib{'hpsw'}{size} = '.1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.5.1';
    $mib{'hpsw'}{used} = '.1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.7.1';
    $mib{'hpsw'}{free} = '.1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6.1';


# boksinfo
    $mib{boksinfo}{sysDescr} = '.1.3.6.1.2.1.1.1';
    $mib{boksinfo}{serial}   = '.1.3.6.1.4.1.9.5.1.2.17';

# memory (bytes) og flash (bytes):

    $mib{mem}{name} = '.1.3.6.1.4.1.9.9.48.1.1.1.2';
    $mib{mem}{used} = '.1.3.6.1.4.1.9.9.48.1.1.1.5';
    $mib{mem}{free} = '.1.3.6.1.4.1.9.9.48.1.1.1.6';

    $mib{flash}{name} = '.1.3.6.1.4.1.9.9.10.1.1.4.1.1.10';
    $mib{flash}{size} = '.1.3.6.1.4.1.9.9.10.1.1.4.1.1.4';
    $mib{flash}{free} = '.1.3.6.1.4.1.9.9.10.1.1.4.1.1.5';

#####

%catswModulType = (1,"other",2,"empty",3,"wsc1000",4,"wsc1001",5,"wsc1100",11,"wsc1200",
                 12,"wsc1400",13,"wsx1441",14,"wsx1450",16,"wsx1483",17,"wsx1454",18,"wsx1455",
                 19,"wsx1431",20,"wsx1465",21,"wsx1436",22,"wsx1434",23,"wsx5009",24,"wsx5013",
                 25,"wsx5011",26,"wsx5010",27,"wsx5113",28,"wsx5101",29,"wsx5103",30,"wsx5104",
                 31,"wsx5105",32,"wsx5155",33,"wsx5154",34,"wsx5153",35,"wsx5111",36,"wsx5213",
                 37,"wsx5020",38,"wsx5006",39,"wsx5005",40,"wsx5509",41,"wsx5506",42,"wsx5505",
                 43,"wsx5156",44,"wsx5157",45,"wsx5158",46,"wsx5030",47,"wsx5114",48,"wsx5223",
                 49,"wsx5224",50,"wsx5012",52,"wsx5302",53,"wsx5213a",55,"wsx5201",56,"wsx5203",
                 57,"wsx5530",66,"wsx5166",67,"wsx5031");




}

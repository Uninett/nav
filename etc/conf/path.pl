#!/usr/bin/perl

use strict;

sub collect{
    return "/usr/local/nav/navme/cron/collect";
}

sub lib{
    return "/usr/local/nav/navme/lib";
}

sub localkilde{
    return "/usr/local/nav/local/etc/kilde/";
}

sub navmekilde{
    return "/usr/local/nav/navme/etc/kilde/";
}

sub localconf{
    return "/usr/local/nav/local/etc/conf";
}
return 1;

%define version 3.0_beta8
%define _prefix /usr/local/nav

Summary: Powerful network administration tool
Name: nav
Version: %{version}
Release: 1
Vendor: NTNU ITEA
Distribution: Network Administration Visualized
URL: http://metanav.ntnu.no/
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/Internet
BuildRoot: %{_builddir}/%{name}-buildroot
BuildArch: noarch
Prefix: %{_prefix}
Requires: bind-utils
Requires: postgresql >= 7.3
Requires: python >= 2.2
Requires: perl >= 5.6
#Requires: java2 >= 1.4
#Requires: java2 >= 1.4

%description
This package contains Network Administration Visualized, an advanced
software suite to monitor large computer networks. It automatically
discovers network topology, monitors network load and outages, and can
send alerts on network events by e-mail and SMS, allowing for flexible
configuration of alert profiles.

%prep
%setup -q

%build
./configure --prefix=%{_prefix}
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

%clean
rm -rf $RPM_BUILD_ROOT

%pre
if ( ! grep -q  "^nav:" /etc/group ); then
  echo Creating group nav
  groupadd nav
fi
if ( ! grep -q  "^navcron:" /etc/passwd ); then
  echo Creating user navcron
  useradd -M -g nav -d %{_prefix} navcron
fi

%post
# Most processes are now run by  navcron, so we make sure any existing
# logfiles and pidfiles are owned by navcron and not root.
if ( test -d %{_prefix}/var/log ); then
  chown -R navcron %{_prefix}/var/log
fi
if ( test -d %{_prefix}/var/run ); then
  chown -R navcron %{_prefix}/var/run
fi

%files
%defattr(-,root,nav)
%{_prefix}/doc
%docdir %{_prefix}/doc
%{_prefix}/lib
%{_prefix}/apache
%defattr(2775,root,nav)
%{_prefix}/var
%defattr(755,root,nav)
%{_prefix}/bin
%{_prefix}/etc/init.d/
%defattr(0775,root,nav)
%dir %{_prefix}/etc
%dir %{_prefix}/etc/report
%dir %{_prefix}/etc/webfront
%dir %{_prefix}/etc/cron.d
%defattr(0664,root,nav)
%config(noreplace) %{_prefix}/etc/alertengine.cfg
%config(noreplace) %{_prefix}/etc/alertmsg.conf
%config(noreplace) %{_prefix}/etc/cricketoids.txt
%config(noreplace) %{_prefix}/etc/cricket-views.conf
%config(noreplace) %{_prefix}/etc/db.conf
%config(noreplace) %{_prefix}/etc/devbrowser.conf
%config(noreplace) %{_prefix}/etc/seeddb.conf
%config(noreplace) %{_prefix}/etc/eventEngine.conf
%config(noreplace) %{_prefix}/etc/getBoksMacs.conf
%config(noreplace) %{_prefix}/etc/getDeviceData.conf
%config(noreplace) %{_prefix}/etc/logger.conf
%config(noreplace) %{_prefix}/etc/machinetracker.conf
%config(noreplace) %{_prefix}/etc/nav.conf
%config(noreplace) %{_prefix}/etc/pg_backup.conf
%config(noreplace) %{_prefix}/etc/pping.conf
%config(noreplace) %{_prefix}/etc/rrdBrowser.conf
%config(noreplace) %{_prefix}/etc/servicemon.conf
%config(noreplace) %{_prefix}/etc/smsd.conf
%config(noreplace) %{_prefix}/etc/vPServer.conf
%config(noreplace) %{_prefix}/etc/report/front.html
%config(noreplace) %{_prefix}/etc/report/report.conf
%config(noreplace) %{_prefix}/etc/report/matrix.conf
%config(noreplace) %{_prefix}/etc/webfront/contact-information.txt
%config(noreplace) %{_prefix}/etc/webfront/external-links.txt
%config(noreplace) %{_prefix}/etc/webfront/nav-links.conf
%config(noreplace) %{_prefix}/etc/webfront/webfront.conf
%config(noreplace) %{_prefix}/etc/webfront/welcome-anonymous.txt
%config(noreplace) %{_prefix}/etc/webfront/welcome-registered.txt
%config(noreplace) %{_prefix}/etc/cron.d/*


%changelog
* Wed Jul 21 2004  <morten.vold@itea.ntnu.no>

- Grabbed new version 3.0_beta7

* Sat Jun 05 2004  <kreide@online.no>

- Copy vPServer to config

* Thu May 27 2004  <kreide@online.no>

- Grabbed new version 3.0_beta5.
- Updated NAV description

* Tue May 11 2004  <morten.vold@itea.ntnu.no>

- (Finally) Grabbed new version 3.0_beta4.

* Wed Mar 24 2004  <morten.vold@itea.ntnu.no>

- Grabbed new version 3.0_beta3.

* Thu Mar 11 2004  <morten.vold@itea.ntnu.no>

- Grabbed new version 3.0_beta2.

* Tue Mar 09 2004  <morten.vold@itea.ntnu.no>

- Some files weren't updated before first beta release was rolled.

* Tue Mar 09 2004  <morten.vold@itea.ntnu.no>

- First beta release.


%define version 3.0_devel
%define _prefix /usr/local/nav

Summary: Powerful network administration tool
Name: nav
Version: %{version}
Release: 4
Vendor: NTNU ITEA
Distribution: Network Administration Visualized
URL: http://metanav.ntnu.no/
Source0: %{name}-%{version}.tar.gz
License: Proprietary
Group: Applications/Internet
BuildRoot: %{_builddir}/%{name}-buildroot
Prefix: %{_prefix}

%description
This package contains a development version of Network Administration Visualized.
This space should contain an interesting description of NAV

%prep
%setup -q

%build
./configure --prefix=%{_prefix}
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install
cp etc/crontab_navcron.nav ${RPM_BUILD_ROOT}%{_prefix}/etc
cp doc/conf/nav.conf ${RPM_BUILD_ROOT}%{_prefix}/etc
cp doc/conf/db.conf ${RPM_BUILD_ROOT}%{_prefix}/etc
extra=`find bin/ -name '*.sh'`
for file in $extra
do
  install -v -m 755 -D $file ${RPM_BUILD_ROOT}%{_prefix}/$file
done

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

%files
%defattr(-,root,nav)
%doc README doc/sql/*.sql
/tmp/*
%{_prefix}/lib
%{_prefix}/apache
%defattr(2775,root,nav)
%{_prefix}/var
%defattr(755,root,nav)
%{_prefix}/bin
%{_prefix}/etc/init.d/
%defattr(2775,root,nav)
%defattr(0775,root,nav)
%dir %{_prefix}/apache/tools
%dir %{_prefix}/etc
%dir %{_prefix}/etc/report
%dir %{_prefix}/etc/webfront
%defattr(0664,root,nav)
%config(noreplace) %{_prefix}/etc/nav.conf
%config(noreplace) %{_prefix}/etc/db.conf
%config(noreplace) %{_prefix}/etc/crontab_navcron.nav
%config(noreplace) %{_prefix}/etc/alertengine.cfg
%config(noreplace) %{_prefix}/etc/alertmsg.conf
%config(noreplace) %{_prefix}/etc/cricketoids.txt
%config(noreplace) %{_prefix}/etc/devbrowser.conf
%config(noreplace) %{_prefix}/etc/eventEngine.conf
%config(noreplace) %{_prefix}/etc/getBoksMacs.conf
%config(noreplace) %{_prefix}/etc/getDeviceData.conf
%config(noreplace) %{_prefix}/etc/machinetracker.conf
%config(noreplace) %{_prefix}/etc/pping.conf
%config(noreplace) %{_prefix}/etc/report/front.html
%config(noreplace) %{_prefix}/etc/report/report.conf
%config(noreplace) %{_prefix}/etc/servicemon.conf
%config(noreplace) %{_prefix}/etc/smsd.conf
%config(noreplace) %{_prefix}/etc/webfront/contact-information.txt
%config(noreplace) %{_prefix}/etc/webfront/external-links.txt
%config(noreplace) %{_prefix}/etc/webfront/nav-links.conf
%config(noreplace) %{_prefix}/etc/webfront/webfront.conf
%config(noreplace) %{_prefix}/etc/webfront/welcome-anonymous.txt
%config(noreplace) %{_prefix}/etc/webfront/welcome-registered.txt


%changelog
* Fri Jan 30 2004  <morten.vold@itea.ntnu.no>

- Another release to fix bugs.  Some web systems were importing
  templates from the wrong places, and maintengine.py did not identify
  itself as a python script.  Configuration files are now tagged with
  the noreplace option.

* Thu Jan 29 2004  <morten.vold@itea.ntnu.no>

- Fixed several problems that only appeared on a clean install.

* Wed Jan 28 2004  <morten.vold@itea.ntnu.no>

- Initial build.

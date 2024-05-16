# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog format was introduced in NAV 5.4.0. Older changelogs can be
found in the [HISTORY](HISTORY) file.

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/Uninett/Argus/tree/master/changelog.d/>.

<!-- towncrier release notes start -->

## [5.10.0] - 2024-05-16


### Removed

- Removed references to IRC support channel from documentation, as the channel
  is closing down ([#2907](https://github.com/Uninett/nav/issues/2907))

### Deprecated

- Support for Python versions older than 3.9 will be dropped in NAV 5.11.

### Added

- New ipdevpoll plugin to fetch ARP cache data from Palo Alto firewall APIs
  ([#2613](https://github.com/Uninett/nav/issues/2613))
- Introduced `towncrier` to aid in collaborative NAV changelog authoring
  ([#2869](https://github.com/Uninett/nav/issues/2869))
- Add library utilities to produce QR codes to arbitrary URLs, for use in
  upcoming features ([#2887](https://github.com/Uninett/nav/issues/2887))
- Added towncrier to automatically produce changelog

### Changed

- Change the Docker Compose-based development environment to use more build
  caching and avoid running too many things as root
  ([#2859](https://github.com/Uninett/nav/issues/2859))
- Changed required PostgreSQL version to 11

### Fixed

- Avoid running command line scripts twice on every invocation
  ([#2877](https://github.com/Uninett/nav/issues/2877),
  [#2878](https://github.com/Uninett/nav/pull/2878))
- Fixed `full-nav-restore.sh` developer helper script that broke after Docker
  Compose development was reorganized
  ([#2888](https://github.com/Uninett/nav/issues/2888))
- Fix missing delete icon in form selector labels
  ([#2898](https://github.com/Uninett/nav/issues/2898))



## [5.9.1] - 2024-03-15

### Fixed

- Fixed broken `navclean` and `navsynctypes`  scripts ([#2875](https://github.com/Uninett/nav/pull/2875), [#2874](https://github.com/Uninett/nav/issues/2874))

## [5.9.0] - 2024-03-08

### Added

- Added option to enable secure cookies in new web security section of `webfront.conf` ([#2194](https://github.com/Uninett/nav/issue/2194), [#2815](https://github.com/Uninett/nav/pull/2815))
- Made `mod_auth_mellon` (SAML) work for logins ([#2740](https://github.com/Uninett/nav/pull/2740))
  - Also added howto for setting up `mod_auth_mellon` for Feide authentication.

### Fixed

- Cycle session IDs on login/logout to protect against potential session fixation attacks ([#2804](https://github.com/Uninett/nav/issues/2804), [#2813](https://github.com/Uninett/nav/pull/2813), [#2836](https://github.com/Uninett/nav/pull/2836), [#2835](https://github.com/Uninett/nav/pull/2835))
- Flush sessions on logout ([#2828](https://github.com/Uninett/nav/pull/2828))
- Prevent clickjacking attacks on NAV by disallowing putting NAV site in document frames ([#2816](https://github.com/Uninett/nav/pull/2816), [#2817](https://github.com/Uninett/nav/pull/2817))
- Cleaned up overview/intro docs ([#2827](https://github.com/Uninett/nav/pull/2827))
- Various cleanups of the test suites:
  - Remove `FakeSession` redundancy ([#2841](https://github.com/Uninett/nav/issues/2841), [#2842](https://github.com/Uninett/nav/pull/2842))
  - Fixed activeipcollector `get_timestamp` function implementation and its broken timezone-naive test ([#2831](https://github.com/Uninett/nav/pull/2831))
  - Fixed broken statemon tests ([#2832](https://github.com/Uninett/nav/pull/2832))
  - Fixed warnings during integration tests ([#2847](https://github.com/Uninett/nav/issues/2847), [#2858](https://github.com/Uninett/nav/pull/2858))
  - Preserve 500-errors in webcrawler tests ([#2861](https://github.com/Uninett/nav/pull/2861))
- Removed nonsensical pydantic requirement ([#2867](https://github.com/Uninett/nav/pull/2867))
- Removed warnings when building docs ([#2856](https://github.com/Uninett/nav/pull/2856))

### Changed

- Modernize installation of NAV scripts/binaries using `pyproject.toml` ([#2676](https://github.com/Uninett/nav/issues/2676), [#2679](https://github.com/Uninett/nav/pull/2679))
- Changed the documentation theme from "Bootstrap" to "Read The Docs", as the Bootstrap theme was no longer being maintained.  This also avoids unnecessary JavaScript libraries in the docs ([#2805](https://github.com/Uninett/nav/issues/2805), [#2825](https://github.com/Uninett/nav/pull/2825), [#2824](https://github.com/Uninett/nav/pull/2824), [#2834](https://github.com/Uninett/nav/issues/2834), [#2837](https://github.com/Uninett/nav/pull/2837), [#2833](https://github.com/Uninett/nav/issues/2833), [#2853](https://github.com/Uninett/nav/pull/2853), [#2868](https://github.com/Uninett/nav/pull/2868))
- Various changes needed to move NAV closer to being fully compatible with Python 3.11:
  - Replaced all uses of `pkg_resources` with `importlib` ([#2791](https://github.com/Uninett/nav/issues/2791), [#2798](https://github.com/Uninett/nav/pull/2798), [#2799](https://github.com/Uninett/nav/pull/2799))
  - Upgraded Twisted to a version that supports Python 3.11 ([#2792](https://github.com/Uninett/nav/issues/2792), [#2796](https://github.com/Uninett/nav/pull/2796))
  - Upgraded psycopg to 2.9.9 ([#2793](https://github.com/Uninett/nav/issues/2793), [#2795](https://github.com/Uninett/nav/pull/2795))
  - Dropped code that was there to support Django's older than 3.2 ([#2823](https://github.com/Uninett/nav/pull/2823))
  - Upgraded `python-ldap` from 3.4.0->3.4.4 ([#2830](https://github.com/Uninett/nav/pull/2830))
  - Enabled running test suite on Python 3.10 by default ([#2838](https://github.com/Uninett/nav/pull/2838))
  - Stopped running test suite on Python 3.8 by default ([#2851](https://github.com/Uninett/nav/pull/2851))
  - Fixed invalid/deprecated backslash escapes in MIB dump files, as warned about in newer Python versions ([#2846](https://github.com/Uninett/nav/pull/2846), [#2848](https://github.com/Uninett/nav/pull/2848))
  - Fixed deprecation warning for Django 4.0 in test suite ([#2844](https://github.com/Uninett/nav/pull/2844))
  - Removed an adaption to Pythons older than 3.7 ([#2840](https://github.com/Uninett/nav/pull/2840))
  - Install Node/NPM in docker dev environment ([#2855](https://github.com/Uninett/nav/pull/2855))
  - Vendor the PickleSerializer ([#2866](https://github.com/Uninett/nav/pull/2866))

## [5.8.4] - 2023-12-14

### Fixed

- Allow admins to configure ports with invalid or unset native VLANs in PortAdmin ([#2477](https://github.com/Uninett/nav/issues/2477), [#2786](https://github.com/Uninett/nav/pull/2786))
- Fix bug that caused PoE config to be completely disabled for Cisco devices where at least one port did not support PoE ([#2781](https://github.com/Uninett/nav/pull/2781))
- Fix PortAdmin save button moving around for ports without PoE support ([#2782](https://github.com/Uninett/nav/pull/2782))
- Fix PortAdmin bug that prevented switching PoE state back and forth without reloading entire page ([#2785](https://github.com/Uninett/nav/pull/2785))
- Fix regression that caused maintenance tasks to be un-editable ([#2783](https://github.com/Uninett/nav/issues/2783), [#2784](https://github.com/Uninett/nav/pull/2784))

## [5.8.3] - 2023-12-01

### Fixed

- Fix non-working SNMPv1 communication ([#2772](https://github.com/Uninett/nav/issues/2772), [#2779](https://github.com/Uninett/nav/issues/2779), [#2780](https://github.com/Uninett/nav/pull/2780))

## [5.8.2] - 2023-11-30

### Fixed

- Fix broken "operate as user" function in User and API Administration tool ([#2766](https://github.com/Uninett/nav/issues/2766), [#2777](https://github.com/Uninett/nav/pull/2777))
- Fix crashing PDU widget ([#2776](https://github.com/Uninett/nav/pull/2776))
- Fix bug that caused PortAdmin to stop working for Cisco switches ([#2773](https://github.com/Uninett/nav/issues/2773), [#2774](https://github.com/Uninett/nav/pull/2774))


## [5.8.1] - 2023-11-29

### Fixed

- Constrain version of 3rd party module `ciscoconfparse`, in order to avoid NAV not working under Python 3.7 ([#2770](https://github.com/Uninett/nav/issues/2770), [#2771](https://github.com/Uninett/nav/pull/2771))
- Fix ipdevpoll crash error from using SNMP v2c profile example that came with NAV ([#2767](https://github.com/Uninett/nav/issues/2767), [#2768](https://github.com/Uninett/nav/pull/2768))
- Gracefully handle encoding errors in invalid sysname/IP input in SeedDB IP Device form ([#2764](https://github.com/Uninett/nav/pull/2764))
- Gracefully handle errors from invalid profiles list input in SeedDB IP Device form ([#2765](https://github.com/Uninett/nav/pull/2765))

## [5.8.0] - 2023-11-24

### Added

- Initial SNMPv3 support added to most parts of NAV
  - Add an SNMPv3 management profile type ([#2693](https://github.com/Uninett/nav/issues/2693), [#2699](https://github.com/Uninett/nav/pull/2699))
  - Add SNMPv3 session support to the synchronous SNMP libraries used by most parts of NAV except ipdevpoll ([#2700](https://github.com/Uninett/nav/issues/2700), [#2710](https://github.com/Uninett/nav/pull/2710))
  - Add SNMPv3 reachability tests in SeedDB IP Device registration forms ([#2704](https://github.com/Uninett/nav/issues/2704), [#2734](https://github.com/Uninett/nav/pull/2734), [#2727](https://github.com/Uninett/nav/issues/2727), [#2730](https://github.com/Uninett/nav/pull/2730))
  - Add SNMPv3 support to Portadmin ([#2712](https://github.com/Uninett/nav/issues/2712), [#2731](https://github.com/Uninett/nav/pull/2731))
  - Add SNMPv3 support to `navsnmp` command line program ([#2724](https://github.com/Uninett/nav/issues/2724), [#2725](https://github.com/Uninett/nav/pull/2725))
  - Add SNMPv3 support to Arnold ([#2726](https://github.com/Uninett/nav/issues/2726), [#2733](https://github.com/Uninett/nav/pull/2733))
  - Add SNMPv3 session support to ipdevpoll's asynchronous SNMP libraries ([#2736](https://github.com/Uninett/nav/issues/2736), [#2743](https://github.com/Uninett/nav/pull/2743))
  - Add SNMPv3 support to`navoidverify` and `naventity` command line programs ([#2747](https://github.com/Uninett/nav/issues/2747), [#2748](https://github.com/Uninett/nav/pull/2748))
- Power-over-Ethernet configuration support for Cisco and Juniper equipment in PortAdmin ([#2632](https://github.com/Uninett/nav/issues/2632), [#2633](https://github.com/Uninett/nav/issues/2633), [#2666](https://github.com/Uninett/nav/pull/2666), [#2635](https://github.com/Uninett/nav/pull/2635), [#2759](https://github.com/Uninett/nav/pull/2759))
- Extract VLAN association from router port names on Checkpoint firewalls ([#2684](https://github.com/Uninett/nav/issues/2684), [#2701](https://github.com/Uninett/nav/pull/2701))
- Add link to our GitHub discussion forums in "Getting help" documentation ([#2746](https://github.com/Uninett/nav/pull/2746))
- Add subcommand to `navuser` command line program for deleting users ([#2705](https://github.com/Uninett/nav/pull/2705))
- Add toggle in `webfront.conf` for automatic creation of remote users ([#2698](https://github.com/Uninett/nav/issue/2698), [#2707](https://github.com/Uninett/nav/pull/2707))
- Add proper documentation index page for all howto guides ([#2716](https://github.com/Uninett/nav/pull/2716))
- Add description to threshold alarms ([#2691](https://github.com/Uninett/nav/issue/2691), [#2709](https://github.com/Uninett/nav/pull/2709))


#### Developer-centric additions

- Add tests for overview of alert profiles page  ([#2741](https://github.com/Uninett/nav/pull/2741))
- Add make rule for cleaning `doc` directory ([#2717](https://github.com/Uninett/nav/pull/2717))
- Add an snmpd service container for SNMPv3 comms testing ([#2697](https://github.com/Uninett/nav/pull/2697))

### Fixed

- Improve validation of maintenance form input in order to avoid unintentional crash reports ([#2757](https://github.com/Uninett/nav/pull/2757))
- Handle invalid alert profile ID form input without crashing ([#2756](https://github.com/Uninett/nav/pull/2756))
- Prevent crash errors in esoteric situations where multiple dashboards have been erroneously marked as a user's default dashboard ([#2680](https://github.com/Uninett/nav/pull/2680))
- Fix broken `navoidverify` command on Linux ([#2737](https://github.com/Uninett/nav/pull/2737))
- Several regressions related to input validation in Alert Profiles were fixed:
  - Fix regression that prevented filter groups from being deleted from an alert profile ([#2729](https://github.com/Uninett/nav/pull/2729))
  - Fix regression that prevented activation/deactivation of alert profiles ([#2732](https://github.com/Uninett/nav/pull/2732))
  - Fix form validation with "equal" and "in" operators for adding expression with group to filter ([#2750](https://github.com/Uninett/nav/pull/2750))
  - Add more expression operator tests for alert profiles and fix cleaning in `ExpressionForm` ([#2752](https://github.com/Uninett/nav/pull/2752))

#### Developer-centric fixes

- Restructure alert profile tests ([#2739](https://github.com/Uninett/nav/pull/2739))

### Changed

- Allow write-enabled SNMP profiles to be used for reading when device has no read-only SNMP profiles ([#2735](https://github.com/Uninett/nav/issues/2735), [#2751](https://github.com/Uninett/nav/pull/2751))
- Improved howto guide for setting up remote user authentication using `mod_auth_oidc` ([#2708](https://github.com/Uninett/nav/pull/2708))

#### Developer-centric changes

- Refactored web authentication code in preparation for future changes to authentication flow ([#2706](https://github.com/Uninett/nav/pull/2706))

### Removed

#### Developer-centric removals

- Remove remaining uses of `Netbox.snmp_version` ([#2522](https://github.com/Uninett/nav/issues/2522))
- Remove unused function `snmp_parameter_factory` ([#2753](https://github.com/Uninett/nav/pull/2753))
- Remove deprecated Netbox SNMP properties ([#2754](https://github.com/Uninett/nav/pull/2754), [#2761](https://github.com/Uninett/nav/pull/2761))



## [5.7.1] - 2023-09-18

### Fixed

- Fixed regression that caused Netmap to be unusable in 5.7.0 ([#2681](https://github.com/Uninett/nav/issues/2681), [#2683](https://github.com/Uninett/nav/pull/2683))

## [5.7.0] - 2023-09-07

### Added

- Even more complex and flexible configuration of NAV logging is now supported through `logging.yml` ([#2659](https://github.com/Uninett/nav/pull/2659))
- Added howto guide for log configuration ([#2660](https://github.com/Uninett/nav/pull/2660))
- Currently non-functional (aka. "blacklisted") alert sender mechanisms are now flagged in the Alert Profiles tool wherever an affected alert address is displayed ([#2653](https://github.com/Uninett/nav/issues/2653), [#2664](https://github.com/Uninett/nav/issues/2664), [#2677](https://github.com/Uninett/nav/pull/2677), [#2678](https://github.com/Uninett/nav/pull/2678))
- Added support for polling and alerting on Juniper chassis and system alerts ([#2358](https://github.com/Uninett/nav/issues/2358), [#2388](https://github.com/Uninett/nav/pull/2388))
  - Juniper only provides alert counters via SNMP, no alert details, unfortunately.
  - Since NAV doesn't support alert state updates, a new eventengine plugin handles alert count transitions by resolving old alerts and creating new ones ([#2432](https://github.com/Uninett/nav/issues/2432), [#2519](https://github.com/Uninett/nav/pull/2519))
- Added a new `contains_address` filter to the `prefix` API endpoint, to enable lookup of matching prefix/vlan details from a single IP or subnet address ([#2577](https://github.com/Uninett/nav/issues/2577), [#2578](https://github.com/Uninett/nav/pull/2578))
- Defined and added abstract methods for Power-over-Ethernet configuration to PortAdmin management handler classes ([#2636](https://github.com/Uninett/nav/pull/2636))
  - These are needed for the upcoming vendor specific implementations of PoE config in PortAdmin.
- Implemented configuration file parsing for upcoming local JWT token feature ([#2568](https://github.com/Uninett/nav/pull/2568))

### Fixed

#### User-visible fixes

- Properly dispose of outgoing alert notifications to invalid alert addresses ([#2661](https://github.com/Uninett/nav/pull/2661))
- Fixed crash when attempting to log device errors with an empty comment in the Device History tool ([#2579](https://github.com/Uninett/nav/issues/2579), [#2580](https://github.com/Uninett/nav/pull/2580))
- Fixed bad styling and missing linebreaks in traceback section of the 500 error page ([#2607](https://github.com/Uninett/nav/issues/2607), [#2628](https://github.com/Uninett/nav/pull/2628))
- Show help text instead of error when running `nav` command without arguments ([#2601](https://github.com/Uninett/nav/issues/2601), [#2603](https://github.com/Uninett/nav/pull/2603))
- Prevent users from entering invalid `sysObjectID` values when editing Netbox types in SeedDB ([#2584](https://github.com/Uninett/nav/pull/2584), [#2566](https://github.com/Uninett/nav/issues/2566))
- Removed upper version bound for *Pillow* image manipulation library, to fix security warnings ([#2567](https://github.com/Uninett/nav/pull/2567))
- Alerts that cannot be sent due to blacklisted media plugins will no longer fill up `alertengine.log` every 30 seconds, unless DEBUG level logging is enabled ([#1787](https://github.com/Uninett/nav/issues/1787), [#2652](https://github.com/Uninett/nav/pull/2652))
- DNS lookups in ipdevinfo are now properly case insensitive ([#2615](https://github.com/Uninett/nav/issues/2615), [#2650](https://github.com/Uninett/nav/pull/2650))
- Alert Profiles will now properly require Slack alert addresses to be valid URLs ([#2657](https://github.com/Uninett/nav/pull/2657))
- 5 minute and 15 minute load average values will now be collected correctly for Juniper devices ([#2671](https://github.com/Uninett/nav/issues/2671), [#2672](https://github.com/Uninett/nav/pull/2672))
- Fix cabling API, which broke due to internal refactorings ([#2621](https://github.com/Uninett/nav/pull/2621))
- Only install NAV's custom `epollreactor2` in ipdevpoll if running on Linux ([#2503](https://github.com/Uninett/nav/issues/2503), [#2604](https://github.com/Uninett/nav/pull/2604))
  - Stops ipdevpoll from crashing on BSDs.

#### Developer-centric fixes

- Moved more of NAV's packaging definition to `pyproject.toml` ([#2655](https://github.com/Uninett/nav/pull/2655))
- Pin pip to version 23.1.0 for CI pipelines to continue working ([#2647](https://github.com/Uninett/nav/pull/2647))
- Improve ipdevpoll logging of SQL queries and from Twisted library ([#2640](https://github.com/Uninett/nav/pull/2640))
- Stop making skipped validation tests for non HTML content ([#2623](https://github.com/Uninett/nav/pull/2623))
- Version-locked indirect dependencies of test suites ([#2622](https://github.com/Uninett/nav/pull/2622), [#2617](https://github.com/Uninett/nav/issues/2617))
- Improve SNMP forwarding/proxying container setup, including adding IPv6 support ([#2637](https://github.com/Uninett/nav/pull/2637), [#2516](https://github.com/Uninett/nav/pull/2516))
- Documented a recipe for establishing SNMP tunnels when testing devices on otherwise unreachable networks ([#2426](https://github.com/Uninett/nav/issues/2426), [#2435](https://github.com/Uninett/nav/pull/2435))
- Run Django development web server in "insecure" mode to improve simulation of a production environment when debug flag is turned off ([#2625](https://github.com/Uninett/nav/pull/2625))
- Added a proper docstring to `bootstrap_django()` function ([#2619](https://github.com/Uninett/nav/pull/2619), [#2168](https://github.com/Uninett/nav/issues/2168))
- Stop restoring stale tox environment caches in GitHub workflows ([#2605](https://github.com/Uninett/nav/pull/2605))
- Added tests for ipdevpoll worker euthanization ([#2599](https://github.com/Uninett/nav/pull/2599), [#2548](https://github.com/Uninett/nav/issues/2548))
- Added tests to ensure snmptrapd can properly look up a NAV router that sends traps from one of its non-management IP addresses ([#2500](https://github.com/Uninett/nav/issues/2500), [#2510](https://github.com/Uninett/nav/pull/2510))
- Avoid redundant graphite time formatting strings by re-using constant ([#2588](https://github.com/Uninett/nav/pull/2588), [#2543](https://github.com/Uninett/nav/issues/2543))
- Make detection of running in a virtualenv more compatible with modern toolchain ([#2573](https://github.com/Uninett/nav/pull/2573))
- Revert to having tox run its own dependency installer ([#2572](https://github.com/Uninett/nav/pull/2572))
- Added explicit back-relation names for several Django ORM models ([#2544](https://github.com/Uninett/nav/pull/2544), [#2546](https://github.com/Uninett/nav/pull/2546), [#2547](https://github.com/Uninett/nav/pull/2547), [#2549](https://github.com/Uninett/nav/pull/2549), [#2550](https://github.com/Uninett/nav/pull/2550), [#2551](https://github.com/Uninett/nav/pull/2551))

## [5.6.1] - 2023-03-23

### Added

#### Developer-centric features
- Document a recipe for establishing SNMP tunnels using socat/SSH ([#2426](https://github.com/Uninett/nav/issues/2426), [#2435](https://github.com/Uninett/nav/pulls/2435))
- Updated/added explicit relation names to various ORM models ([#2544](https://github.com/Uninett/nav/pull/2544), [#2546](https://github.com/Uninett/nav/pull/2546), [#2547](https://github.com/Uninett/nav/pull/2547), [#2549](https://github.com/Uninett/nav/pull/2549), [#2550](https://github.com/Uninett/nav/pull/2550), [#2551](https://github.com/Uninett/nav/pull/2551), [#2595](https://github.com/Uninett/nav/pull/2595), [#2596](https://github.com/Uninett/nav/pull/2596))
- Added tests for simple searches ([#2597](https://github.com/Uninett/nav/pull/2597))

### Fixed

#### User-visible fixes
- Ensure event variables are always posted in transactions, so the event engine does not accidentally end up processing incomplete event information ([#2594](https://github.com/Uninett/nav/pull/2594))
- Report broken cache configuration as an error in Ranked Statistics tool, rather than taking down the whole NAV site ([#2561](https://github.com/Uninett/nav/issues/2561), [#2563](https://github.com/Uninett/nav/pull/2563))
- Show error message on invalid ip address in ipdevinfo ([#2590](https://github.com/Uninett/nav/pull/2590), [#2589](https://github.com/Uninett/nav/issues/2589))
- Link to correct room in room report if room has a space in its name ([#2593](https://github.com/Uninett/nav/pull/2593), [#2592](https://github.com/Uninett/nav/issues/2592))
- Work around duplicate internal serial numbers in Juniper equipment by trusting data only from the device with the lowest entity index ([#2583](https://github.com/Uninett/nav/pull/2583), [#2493](https://github.com/Uninett/nav/issues/2493))
- Make save function in AlertHistory, EventHistory and AlertQueue atomic  ([#2594](https://github.com/Uninett/nav/pull/2594))
- Ignore LDAP server referral responses, rather then erroring out during the login process ([#2576](https://github.com/Uninett/nav/pull/2576), [#1166](https://github.com/Uninett/nav/issues/1166))
- Include the `new_version` variable in alert message templates for device hw/fw/sw upgrades ([#2565](https://github.com/Uninett/nav/pull/2565))
- Update NAV blog widget to use the new blog URL ([#2585](https://github.com/Uninett/nav/pull/2585))
- Handle invalid IP address input in ipdevinfo device searches gracefully, rather then crashing with a 500 error ([#2589](https://github.com/Uninett/nav/issues/2589), [#2590](https://github.com/Uninett/nav/pull/2590))
- Fix broken links to room details from room report for rooms with spaces in their names ([#2592](https://github.com/Uninett/nav/issues/2592), [#2593](https://github.com/Uninett/nav/pull/2593))
- Catch Validation error in filtering of prefixes in API ([#2606](https://github.com/Uninett/nav/issues/2606), [#2608](https://github.com/Uninett/nav/pull/2608))
- Redesign the 500 Error page so that the exception traceback if formatted as one


## [5.6.0] - 2023-01-20

### Added

#### User-visible features

- NAPALM/NETCONF management profiles can now be configured with custom timeout values ([#2460](https://github.com/Uninett/nav/pull/2460), [#2390](https://github.com/Uninett/nav/issues/2390))
- Post lifecycle events the first time new chassis/module/PSU/fan devices are seen ([#2391](https://github.com/Uninett/nav/issues/2391), [#2414](https://github.com/Uninett/nav/pull/2414))
- Accept JSON Web Tokens signed by third-parties as valid API authentication/authorization tokens ([#2483](https://github.com/Uninett/nav/issues/2483), [#2511](https://github.com/Uninett/nav/pull/2511))
- Collect "chassis" serial numbers from Aruba wireless controllers ([#2514](https://github.com/Uninett/nav/pull/2514))
- Added an API endpoint for module information ([#2517](https://github.com/Uninett/nav/issues/2517), [#2520](https://github.com/Uninett/nav/pull/2520))
- Result caching added to ranked statistics - including the ability to populate the cache regularly behind-the-scenes in a cronjob (([#1504](https://github.com/Uninett/nav/issues/1504), [#2398](https://github.com/Uninett/nav/pull/2398))

#### Developer-centric features

- Added `buglog.py` option to fetch issue numbers from git reflog ([#2474](https://github.com/Uninett/nav/pull/2474))
- Added tests for  `get_memory_usage` for all memory MIBs ([#2376](https://github.com/Uninett/nav/issues/2376), [#2441](https://github.com/Uninett/nav/pull/2441))
- Added tests to discover invalid MIB dumps from smidump ([#2501](https://github.com/Uninett/nav/issues/2501), ([#2521](https://github.com/Uninett/nav/pull/2521))
- Updated/added explicit relation names to various ORM models ([#2539](https://github.com/Uninett/nav/pull/2539), [#2540](https://github.com/Uninett/nav/pull/2540), [#2541](https://github.com/Uninett/nav/pull/2541), [#2542](https://github.com/Uninett/nav/pull/2542))

### Fixed

#### User-visible fixes

- Empty alert messages are no longer sent when device software upgrades are detected ([#2533](https://github.com/Uninett/nav/issues/2533))
- Merged two fixes from the 5.4.x stable series that never actually made it into the 5.5 series:
  - Metric values of *0.0* are evaluated correctly by threshold rules ([#2447](https://github.com/Uninett/nav/issues/2447))
  - Validate maintenance calendar input form to avoid e-mail spam from bots scanning for vulnerabilities ([#2420](https://github.com/Uninett/nav/issues/2420), [#2431](https://github.com/Uninett/nav/pull/2431))
- Properly log (for posterity) old and new revision numbers with every software/hardware/firmware upgrade event NAV posts ([#2515](https://github.com/Uninett/nav/pull/2515), [#2545](https://github.com/Uninett/nav/pull/2545), [#2560](https://github.com/Uninett/nav/pull/2560))
- snmpwalk routine for synchronous NAV code now correctly handles end-of-mib-view errors ([#1925](https://github.com/Uninett/nav/issues/1925), [#2489](https://github.com/Uninett/nav/pull/2489))
- Removed deprecation warnings from command line programs `navsnmp`, `naventity` and `navoidverify` ([#2389](https://github.com/Uninett/nav/issues/2389), [#2429](https://github.com/Uninett/nav/pull/2429))

#### Developer-centric fixes

- Use pip-compile's backtracking dependency resolver to fix failing CI pipelines ([#2509](https://github.com/Uninett/nav/pull/2509))
- Updated libsnmp dependency for newer Ubuntu runners in GitHub pipelines ([#2532](https://github.com/Uninett/nav/pull/2532))
- Use same version of Django for pylint runs as the latest stable release ([#2536](https://github.com/Uninett/nav/pull/2536))
- Fixed a slew of new CI pipeline / test suite problems that appear after new years ([#2537](https://github.com/Uninett/nav/pull/2537))

## [5.5.2] - 2022-11-10

### Fixed

- Fix serious collection breakdown in ipdevpoll by re-generating a valid Python representation of CISCO-ENHANCED-MEMPOOL-MIB ([#2494](https://github.com/Uninett/nav/issues/2494), [#2495](https://github.com/Uninett/nav/pull/2495))
- Fix broken trap processing in snmptrapd ([#2497](https://github.com/Uninett/nav/issues/2497), [#2498](https://github.com/Uninett/nav/pull/2498))


## [5.5.1] - 2022-11-09

### Fixed

- Delete and ignore module devices with fake serial number `BUILTIN`, as reported by Juniper equipment, in order to avoid spamming with `device[SFH]wUpgrade` alerts ([#2491](https://github.com/Uninett/nav/issues/2491), [#2492](https://github.com/Uninett/nav/pull/2492))

## [5.5.0] - 2022-11-04

### Changed

- Bump `lxml` from 4.6.5 to 4.9.1 in /tests ([#2443](https://github.com/Uninett/nav/pull/2443))
- Links and documented references to the NAV mailing lists have changed to the `lister.sikt.no` domain.

### Added

- Add link to #nav irc channel on Libera.Chat to README file ([#2475](https://github.com/Uninett/nav/pull/2475))
- Add `mac_addresses` attribute to `/netbox/` API endpoint ([#2487](https://github.com/Uninett/nav/pull/2487), [#2490](https://github.com/Uninett/nav/pull/2490))
- Add ability to filter by alert severity in the status tool ([#2467](https://github.com/Uninett/nav/pull/2467))
- Support for fetching ARP cache entries from all Arista VRF instances ([#2262](https://github.com/Uninett/nav/issues/2262), [#2454](https://github.com/Uninett/nav/pull/2454)))
- Link aggregation information added to NAV API ([#1765](https://github.com/Uninett/nav/issues/1765), [#2440](https://github.com/Uninett/nav/pull/2440))
- Support fetching memory stats from `CISCO-ENHANCED-MEMPOOL-MIB` ([#2236](https://github.com/Uninett/nav/issues/2236), [#2439](https://github.com/Uninett/nav/pull/2439))
- Added a flag to `navcheckservice` that shows all available handler plugins ([#2378](https://github.com/Uninett/nav/issues/2378), [#2437](https://github.com/Uninett/nav/pull/2437))
- Post `deviceHwUpgrade`/`deviceSwUpgrade`/`deviceFwUpgrade` events when changes are detected to devices' hardware, software or firmware revisions ([#2393](https://github.com/Uninett/nav/issues/2393), [#2413](https://github.com/Uninett/nav/pull/2413))
- Call a `cleanup()` method for individual container objects after ipdevpoll save stage ([#2421](https://github.com/Uninett/nav/pull/2421))
- Added `Device` methods to resolve and return related objects/entities (chassis, modules, fans, power supplied) and extended device descriptions ([#2428](https://github.com/Uninett/nav/pull/2428))

### Fixed

- Avoid potential resource leaks by properly closing configuration files after reading them ([#2451](https://github.com/Uninett/nav/pull/2451))
- Geomap "link to this configuration" now actually opens the correct location at the correct zoom level ([#2412](https://github.com/Uninett/nav/issues/2412), [#2488](https://github.com/Uninett/nav/pull/2488))
- snmptrapd can now identify an SNMP agent from any of its interface addresses ([#2387](https://github.com/Uninett/nav/issues/2387), [#2461](https://github.com/Uninett/nav/pull/2461))
- PortAdmin now ignores incorrectly configured VLAN tags (tagged as `NA`) on Juniper switches, instead of crashing ([#2452](https://github.com/Uninett/nav/issues/2452), [#2453](https://github.com/Uninett/nav/pull/2453))
- Fix potential ipdevpoll crashes due to database fetches in wrong thread ([#2478](https://github.com/Uninett/nav/issues/2478), [#2480](https://github.com/Uninett/nav/pull/2480))
- Handle Graphite connection issues gracefully in ranked statistics page ([#2459](https://github.com/Uninett/nav/pull/2459))
- Handle Graphite connection issues gracefully in device group detail page ([#2345](https://github.com/Uninett/nav/issues/2345), [#2434](https://github.com/Uninett/nav/pull/2434))
- Removed needless carbon data chunking from `activeipcollector` ([#1696](https://github.com/Uninett/nav/issues/1696), [#2462](https://github.com/Uninett/nav/pull/2462))
- Evaluate `0.0` as a valid numeric metric value during threshold rule evaluations ([#2447](https://github.com/Uninett/nav/issues/2447)
- Updated dead links in Geomap documentation ([#2419](https://github.com/Uninett/nav/pull/2419))
- Link from IPAM to reserve prefixed in SeedDB now works again ([#2410](https://github.com/Uninett/nav/issues/2410), [#2422](https://github.com/Uninett/nav/pull/2422))
- Improved inefficient database queries in Arnold ([#2425](https://github.com/Uninett/nav/pull/2425))
- Updated tox examples in hacking documentation ([#2427](https://github.com/Uninett/nav/issues/2427), [#2430](https://github.com/Uninett/nav/pull/2430))
- Fixed an `AttributeError` crash bug in the `naventity` command line program ([#2433](https://github.com/Uninett/nav/issues/2433), [#2444](https://github.com/Uninett/nav/pull/2444))

## [5.4.0] - 2022-05-19

### Changed

- The changelog format has changed from the legacy format into one based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- Transceivers are no longer classed as modules ([#1154](https://github.com/Uninett/nav/issues/1154))
- Generate more secure API tokens ([#2366](https://github.com/Uninett/nav/issues/2366))
- Remaining instances of "Uninett" in footer FAQ have changed to Sikt ([#2367](https://github.com/Uninett/nav/pull/2367))
- Upgrade to napalm 3.4.1 ([#2403](https://github.com/Uninett/nav/pull/2403))

### Added

- Support more recent AKCP environment probes ([#2107](https://github.com/Uninett/nav/issues/2107)
- Collect and graph temperature readings from JUNIPER-MIB ([#2342](https://github.com/Uninett/nav/issues/2342))
- Add support for wildcards in report IN operator (a.k.a. `(,,)`) ([#2347](https://github.com/Uninett/nav/issues/2347))
- Get VLAN tag from Juniper chassis cluster redundant ethernet interface ("RETH") names ([#2357](https://github.com/Uninett/nav/issues/2357))
- Collect and graph memory usage from JUNIPER-MIB ([#2359](https://github.com/Uninett/nav/issues/2359))
- Document NAV's various command line utilities ([#2368](https://github.com/Uninett/nav/pull/2368))
- Add a contrib script to ship ISC DHCP server lease stats to NAV's Graphite instance ([#2371](https://github.com/Uninett/nav/issues/2371))

### Fixed

- Don't display JavaScript alert dialog box when generating links to the current Geomap configuration ([#1016](https://github.com/Uninett/nav/issues/1016))
- Optimize SeedDB prefix listing queries ([#2156](https://github.com/Uninett/nav/issues/2156))
- Fix broken deletion of quick links from "My stuff"-menu ([#2334](https://github.com/Uninett/nav/issues/2334))
- Display friendlier Juniper RPC error reports in Portadmin ([#2362](https://github.com/Uninett/nav/issues/2362))
- Get rid of warning: `CacheKeyWarning: Cache key contains characters that will cause errors if used with memcached` ([#2379](https://github.com/Uninett/nav/issues/2379))
- Get rid of warning: `DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated` ([#2381](https://github.com/Uninett/nav/issues/2381))
-  Get rid of warning: `django.contrib.postgres.fields.JSONField is deprecated. Support for it (except in historical migrations) will be removed in Django 4.0.` ([#2382](https://github.com/Uninett/nav/issues/2382))
- Rotate room image thumbnails correctly based on EXIF orientation tag ([#2385](https://github.com/Uninett/nav/issues/2385))
- Fix Django JSONField import deprecation warnings ([#2396](https://github.com/Uninett/nav/pull/2396))
- Fix broken documentation build environment in Read The Docs ([#2399](https://github.com/Uninett/nav/pull/2399))
- Optimize SeedDB room listing queries ([#2400](https://github.com/Uninett/nav/pull/2400))
- Optimize SeedDB netboxtype listing queries ([#2401](https://github.com/Uninett/nav/pull/2401))
- Optimize SeedDB vlan listing queries ([#2402](https://github.com/Uninett/nav/pull/2402))
- Fix broken deserialization of Rack data ([#2407](https://github.com/Uninett/nav/pull/2407))
- Remove unnecessary quotation marks in SeedDB ([#2416](https://github.com/Uninett/nav/pull/2416))
- Fix incorrect handling of stateless event posting in internal APIs ([#2417](https://github.com/Uninett/nav/pull/2417))

### Removed

- Remaining Python 2 compatibility code ([#2319](https://github.com/Uninett/nav/issues/2319))
- Dependency on the `six` Python module

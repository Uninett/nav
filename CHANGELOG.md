# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog format was introduced in NAV 5.4.0. Older changelogs can be
found in the [HISTORY](HISTORY) file.

## [5.6.1] - 2023-03-23

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
- Fix broken links to room details from room report for rooms with spaces in their names ([#2592](https://github.com/Uninett/nav/issues/2592), [#2593](https://github.com/Uninett/nav/pull/2593)))


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

# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog format was introduced in NAV 5.4.0. Older changelogs can be
found in the [HISTORY](HISTORY) file.

## [5.4.0] - 2022-05-19

## Changed

- The changelog format has changed from the legacy format into one based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- Transceivers are no longer classed as modules ([#1154](https://github.com/Uninett/nav/issues/1154))
- Generate more secure API tokens ([#2366](https://github.com/Uninett/nav/issues/2366))
- Remaining instances of "Uninett" in footer FAQ have changed to Sikt ([#2367](https://github.com/Uninett/nav/pull/2367))
- Upgrade to napalm 3.4.1 ([#2403](https://github.com/Uninett/nav/pull/2403))

## Added

- Support more recent AKCP environment probes ([#2107](https://github.com/Uninett/nav/issues/2107)
- Collect and graph temperature readings from JUNIPER-MIB ([#2342](https://github.com/Uninett/nav/issues/2342))
- Add support for wildcards in report IN operator (a.k.a. `(,,)`) ([#2347](https://github.com/Uninett/nav/issues/2347))
- Get VLAN tag from Juniper chassis cluster redundant ethernet interface ("RETH") names ([#2357](https://github.com/Uninett/nav/issues/2357))
- Collect and graph memory usage from JUNIPER-MIB ([#2359](https://github.com/Uninett/nav/issues/2359))
- Document NAV's various command line utilities ([#2368](https://github.com/Uninett/nav/pull/2368))
- Add a contrib script to ship ISC DHCP server lease stats to NAV's Graphite instance ([#2371](https://github.com/Uninett/nav/issues/2371))

## Fixed

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

## Removed

- Remaining Python 2 compatibility code ([#2319](https://github.com/Uninett/nav/issues/2319))
- Dependency on the `six` Python module
